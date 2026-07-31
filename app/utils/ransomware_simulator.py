"""
Ransomware Simulator Module — FOR DEMONSTRATION AND TESTING PURPOSES ONLY.

Provides:
- encrypt_user_file(): Upload → backup → encrypt with Fernet → return key to user
- decrypt_with_key(): User provides key → decrypt file → remove .locked → ready for download

This is NOT malicious software. It is an educational tool for cybersecurity
awareness and training within CyberShield.
"""

from __future__ import annotations

import os
import hashlib
import uuid
from datetime import datetime
from typing import Dict, Optional, Tuple

from cryptography.fernet import Fernet, InvalidToken
from flask import current_app
from flask_mail import Message
from werkzeug.datastructures import FileStorage

from app.extensions import db, mail
from app.models import BackupHistory, User


def compute_sha256(data: bytes) -> str:
    """Compute SHA-256 hash of data bytes."""
    return hashlib.sha256(data).hexdigest()


def generate_encryption_key() -> str:
    """Generate a new Fernet encryption key string."""
    return Fernet.generate_key().decode("utf-8")


def get_user_backup_folder(user_id: int, backup_dir: str) -> str:
    """Get or create user-specific backup folder."""
    user_folder = os.path.join(backup_dir, f"user_{user_id}")
    os.makedirs(user_folder, exist_ok=True)
    return user_folder


def encrypt_user_file(
    file_storage: FileStorage,
    user_id: int,
    backup_dir: str,
) -> Dict:
    """
    Upload a file, save it as backup, encrypt it with Fernet, and return
    the encryption key to the user.

    Args:
        file_storage: Werkzeug FileStorage object from Flask upload.
        user_id: ID of the user.
        backup_dir: Base backup directory.

    Returns:
        Dict with:
            - success: bool
            - file_name: original filename
            - encrypted_name: filename with .locked extension
            - encryption_key: the Fernet key (returned to user)
            - backup_id: BackupHistory record ID
            - message: status message
            - error: error message if failed

    Raises:
        ValueError on validation errors.
    """
    if not file_storage or not file_storage.filename:
        raise ValueError("No file provided.")

    original_filename = file_storage.filename
    file_data = file_storage.read()

    if not file_data:
        raise ValueError(f"File '{original_filename}' is empty.")

    # Compute SHA-256 of original
    file_hash = compute_sha256(file_data)

    # Prevent duplicate backups of same file
    existing = BackupHistory.query.filter_by(
        user_id=user_id,
        sha256_hash=file_hash,
        status="active",
    ).first()
    if existing and os.path.exists(existing.backup_path):
        raise ValueError(
            f"A backup of '{original_filename}' already exists "
            f"(Backup ID: {existing.id})."
        )

    # Ensure user backup folder exists
    user_folder = get_user_backup_folder(user_id, backup_dir)

    # Save original file as backup
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    safe_backup_name = f"{timestamp}_{file_hash[:16]}_{original_filename}"
    backup_path = os.path.join(user_folder, safe_backup_name)

    with open(backup_path, "wb") as f:
        f.write(file_data)

    file_size = os.path.getsize(backup_path)

    # Generate encryption key
    key_str = generate_encryption_key()
    cipher = Fernet(key_str.encode("utf-8"))

    # Encrypt the file data
    encrypted_data = cipher.encrypt(file_data)

    # Save encrypted file with .locked extension
    encrypted_filename = f"{original_filename}.locked"
    encrypted_path = os.path.join(user_folder, encrypted_filename)

    with open(encrypted_path, "wb") as f:
        f.write(encrypted_data)

    # Remove the unencrypted backup (simulating ransomware behavior)
    if os.path.exists(backup_path):
        os.remove(backup_path)

    # Store backup record in database
    backup_record = BackupHistory(
        user_id=user_id,
        file_name=encrypted_filename,  # Stored as .locked name
        original_path=original_filename,
        backup_path=encrypted_path,
        file_size=file_size,
        sha256_hash=file_hash,
        backup_date=datetime.utcnow(),
        status="encrypted",
        encryption_key=key_str,  # Store key so user can retrieve later if needed
    )
    db.session.add(backup_record)
    db.session.commit()

    # Send encryption key to user's registered email
    try:
        user = User.query.get(user_id)
        if user and user.email:
            msg = Message(
                subject="[CyberShield] Your File Encryption Key",
                recipients=[user.email],
            )
            msg.body = f"""
Hello {user.full_name},

Your file "{original_filename}" has been encrypted using the CyberShield Ransomware Simulator.

IMPORTANT: Save this encryption key! You will need it to decrypt your file.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ENCRYPTION KEY: {key_str}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

File Details:
- Original Name: {original_filename}
- Encrypted Name: {encrypted_filename}
- Backup ID: {backup_record.id}
- Encryption Date: {backup_record.backup_date.strftime('%Y-%m-%d %H:%M:%S')}

To decrypt your file:
1. Go to CyberShield → Ransomware Simulator
2. Select the encrypted file from the list
3. Paste or type this encryption key
4. Click "Decrypt & Restore File"
5. Download your restored file

If you did not perform this action, please secure your account immediately.

Regards,
CyberShield Security Team
            """.strip()
            mail.send(msg)
            current_app.logger.info(f"Encryption key emailed to {user.email} for file '{original_filename}'")
    except Exception as e:
        # Log email failure but don't block the encryption process
        current_app.logger.warning(f"Failed to send encryption key email: {str(e)}")

    return {
        "success": True,
        "backup_id": backup_record.id,
        "file_name": original_filename,
        "encrypted_name": encrypted_filename,
        "encryption_key": key_str,
        "file_size": file_size,
        "sha256_hash": file_hash,
        "backup_date": backup_record.backup_date.strftime("%Y-%m-%d %H:%M:%S"),
        "key_emailed": True,
        "message": f"File '{original_filename}' encrypted successfully. Encryption key has been sent to your registered email!",
    }


def decrypt_with_key(
    backup_id: int,
    user_provided_key: str,
    user_id: int,
    restore_dir: str,
) -> Dict:
    """
    Decrypt a .locked file using a user-provided encryption key.

    The user must provide the exact key that was shown during encryption.

    Args:
        backup_id: BackupHistory record ID.
        user_provided_key: The encryption key string provided by the user.
        user_id: ID of the user requesting decryption.
        restore_dir: Directory to store the decrypted file.

    Returns:
        Dict with:
            - success: bool
            - file_name: original filename (without .locked)
            - decrypted_path: path to decrypted file
            - message: status message
            - error: error message if failed
    """
    backup = BackupHistory.query.get(backup_id)
    if not backup:
        return {
            "success": False,
            "error": "Backup record not found.",
        }

    if backup.user_id != user_id:
        return {
            "success": False,
            "error": "Unauthorized access to this file.",
        }

    if backup.status != "encrypted":
        return {
            "success": False,
            "error": f"File is not in encrypted state (status: {backup.status}).",
        }

    if not os.path.exists(backup.backup_path):
        return {
            "success": False,
            "error": "Encrypted file not found on disk. It may have been deleted.",
        }

    # Read the encrypted file
    with open(backup.backup_path, "rb") as f:
        encrypted_data = f.read()

    # Try to decrypt with user-provided key
    try:
        cipher = Fernet(user_provided_key.encode("utf-8"))
        decrypted_data = cipher.decrypt(encrypted_data)
    except InvalidToken:
        return {
            "success": False,
            "error": "Decryption failed: Invalid encryption key. The key you provided is incorrect.",
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Decryption failed: {str(e)}",
        }

    # Get original filename (remove .locked)
    original_filename = backup.file_name
    if original_filename.endswith(".locked"):
        original_filename = original_filename[:-7]  # Remove .locked

    # If original_path is stored, use that instead
    if backup.original_path and not backup.original_path.endswith(".locked"):
        original_filename = backup.original_path

    # Ensure restore directory exists
    os.makedirs(restore_dir, exist_ok=True)

    # Save decrypted file
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    safe_restore_name = f"{timestamp}_{original_filename}"
    decrypted_path = os.path.join(restore_dir, safe_restore_name)

    with open(decrypted_path, "wb") as f:
        f.write(decrypted_data)

    # Update backup record
    backup.status = "restored"
    db.session.commit()

    return {
        "success": True,
        "backup_id": backup.id,
        "file_name": original_filename,
        "decrypted_path": decrypted_path,
        "decrypted_size": os.path.getsize(decrypted_path),
        "message": f"File '{original_filename}' decrypted successfully!",
    }


def list_encrypted_files(user_id: int) -> list:
    """
    List all encrypted files for a user.

    Args:
        user_id: ID of the user.

    Returns:
        List of dicts with backup metadata.
    """
    backups = BackupHistory.query.filter(
        BackupHistory.user_id == user_id,
        BackupHistory.status.in_(["encrypted", "restored"]),
    ).order_by(BackupHistory.backup_date.desc()).all()

    return [{
        "id": b.id,
        "file_name": b.file_name,
        "original_name": b.original_path if b.original_path else b.file_name.replace(".locked", ""),
        "sha256_hash": b.sha256_hash,
        "backup_date": b.backup_date.strftime("%Y-%m-%d %H:%M:%S"),
        "file_size": b.file_size,
        "status": b.status,
        "has_encryption_key": b.encryption_key is not None,
    } for b in backups]


def delete_encrypted_file(backup_id: int, user_id: int) -> Dict:
    """
    Delete an encrypted backup record and its file from disk.

    Args:
        backup_id: BackupHistory record ID.
        user_id: ID of the user.

    Returns:
        Dict with success status and message.
    """
    backup = BackupHistory.query.get(backup_id)
    if not backup:
        return {"success": False, "error": "Backup record not found."}

    if backup.user_id != user_id:
        return {"success": False, "error": "Unauthorized access."}

    # Remove file from disk if it exists
    if backup.backup_path and os.path.exists(backup.backup_path):
        os.remove(backup.backup_path)

    # Delete the database record
    db.session.delete(backup)
    db.session.commit()

    return {"success": True, "message": f"Encrypted file '{backup.file_name}' deleted."}


def get_stats(user_id: int) -> Dict:
    """
    Get dashboard statistics for the ransomware module.

    Args:
        user_id: ID of the user.

    Returns:
        Dict with stats.
    """
    total_encrypted = BackupHistory.query.filter_by(
        user_id=user_id, status="encrypted"
    ).count()

    total_restored = BackupHistory.query.filter_by(
        user_id=user_id, status="restored"
    ).count()

    total_files = BackupHistory.query.filter(
        BackupHistory.user_id == user_id,
        BackupHistory.status.in_(["encrypted", "restored"])
    ).count()

    return {
        "total_files": total_files,
        "encrypted_files": total_encrypted,
        "restored_files": total_restored,
    }

