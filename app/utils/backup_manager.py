"""
Backup Manager — Core backup/restore logic for CyberShield Backup & Ransomware Recovery.

Provides:
- Secure file backup with SHA-256 integrity verification
- Duplicate backup prevention
- Batch restore with integrity checking
- Recovery point management
- Dashboard statistics
"""

from __future__ import annotations

import hashlib
import os
import shutil
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from werkzeug.datastructures import FileStorage

from app.extensions import db
from app.models import BackupHistory, RecoveryHistory


def compute_sha256(filepath: str) -> str:
    """Compute SHA-256 hash of a file."""
    sha = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            sha.update(chunk)
    return sha.hexdigest()


def compute_sha256_bytes(data: bytes) -> str:
    """Compute SHA-256 hash of bytes."""
    return hashlib.sha256(data).hexdigest()


def generate_incident_id() -> str:
    """Generate a unique incident ID."""
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    unique = uuid.uuid4().hex[:8].upper()
    return f"CSIRT-{timestamp}-{unique}"


# =============================================================================
# USER-SPECIFIC BACKUP FOLDER MANAGEMENT
# =============================================================================


def get_user_backup_folder_path(user_id: int, backup_dir: str) -> str:
    """
    Get the path to a user's personal backup folder.

    Args:
        user_id: ID of the user.
        backup_dir: Base backup directory.

    Returns:
        Absolute path to the user's backup folder.
    """
    return os.path.join(backup_dir, f"user_{user_id}")


def create_user_backup_folder(user_id: int, backup_dir: str) -> str:
    """
    Create a user-specific backup folder if it doesn't exist.

    Args:
        user_id: ID of the user.
        backup_dir: Base backup directory.

    Returns:
        Path to the created/existing user backup folder.
    """
    user_folder = get_user_backup_folder_path(user_id, backup_dir)
    os.makedirs(user_folder, exist_ok=True)
    return user_folder


def list_user_backups(user_id: int, backup_dir: str) -> List[Dict]:
    """
    List all backup files in the user's personal backup folder.

    Args:
        user_id: ID of the user.
        backup_dir: Base backup directory.

    Returns:
        List of dicts with file metadata.
    """
    user_folder = get_user_backup_folder_path(user_id, backup_dir)
    if not os.path.exists(user_folder):
        return []

    backups = []
    for fname in os.listdir(user_folder):
        fpath = os.path.join(user_folder, fname)
        if os.path.isfile(fpath):
            stat = os.stat(fpath)
            backups.append({
                "file_name": fname,
                "path": fpath,
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                "sha256": compute_sha256(fpath),
            })

    # Sort by modified time descending
    backups.sort(key=lambda b: b["modified"], reverse=True)
    return backups


def create_backup(
    file_storage: FileStorage,
    user_id: int,
    backup_dir: str,
) -> Dict:
    """
    Create a secure backup of an uploaded file.

    Args:
        file_storage: Werkzeug FileStorage object from Flask upload.
        user_id: ID of the user creating the backup.
        backup_dir: Base directory for storing backups.

    Returns:
        Dict with backup metadata.

    Raises:
        ValueError: If file is empty or duplicate.
    """
    if not file_storage or not file_storage.filename:
        raise ValueError("No file provided.")

    original_filename = file_storage.filename
    file_data = file_storage.read()

    if not file_data:
        raise ValueError(f"File '{original_filename}' is empty.")

    # Compute SHA-256 of the uploaded file
    file_hash = compute_sha256_bytes(file_data)

    # Prevent duplicate backups
    existing = BackupHistory.query.filter_by(
        user_id=user_id,
        sha256_hash=file_hash,
        status="active",
    ).first()

    if existing:
        raise ValueError(
            f"A backup of '{original_filename}' already exists "
            f"(Backup ID: {existing.id}, Date: {existing.backup_date.strftime('%Y-%m-%d %H:%M:%S')})."
        )

    # Create a timestamped subdirectory for this backup
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    safe_name = f"{timestamp}_{file_hash[:16]}_{original_filename}"
    backup_subdir = os.path.join(backup_dir, f"backup_{timestamp}")
    os.makedirs(backup_subdir, exist_ok=True)

    backup_path = os.path.join(backup_subdir, safe_name)

    # Write the file to secure backup storage
    with open(backup_path, "wb") as f:
        f.write(file_data)

    file_size = os.path.getsize(backup_path)

    # Store backup record in database
    backup_record = BackupHistory(
        user_id=user_id,
        file_name=original_filename,
        original_path=original_filename,
        backup_path=backup_path,
        file_size=file_size,
        sha256_hash=file_hash,
        backup_date=datetime.utcnow(),
        status="active",
    )
    db.session.add(backup_record)
    db.session.commit()

    return {
        "id": backup_record.id,
        "file_name": original_filename,
        "backup_path": backup_path,
        "sha256_hash": file_hash,
        "file_size": file_size,
        "backup_date": backup_record.backup_date.strftime("%Y-%m-%d %H:%M:%S"),
        "status": "active",
    }


def restore_from_backup(
    backup_id: int,
    user_id: int,
    restore_dir: str,
) -> Dict:
    """
    Restore a single file from backup with integrity verification.

    Args:
        backup_id: ID of the backup record.
        user_id: ID of the user requesting restore.
        restore_dir: Directory to place restored files.

    Returns:
        Dict with restore result metadata.

    Raises:
        ValueError: If backup not found, unauthorized, or integrity check fails.
    """
    backup = BackupHistory.query.get_or_404(backup_id)

    if backup.user_id != user_id:
        raise ValueError("Unauthorized access to backup.")

    if backup.status != "active":
        raise ValueError(f"Backup is not active (status: {backup.status}).")

    if not os.path.exists(backup.backup_path):
        backup.status = "missing"
        db.session.commit()
        raise ValueError(f"Backup file not found on disk: {backup.file_name}")

    # Verify integrity with SHA-256
    current_hash = compute_sha256(backup.backup_path)
    if current_hash != backup.sha256_hash:
        backup.status = "corrupted"
        db.session.commit()
        raise ValueError(
            f"Backup integrity check FAILED for '{backup.file_name}'. "
            "The backup file has been modified or corrupted."
        )

    # Create restore point directory
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    restore_subdir = os.path.join(restore_dir, f"restore_{timestamp}")
    os.makedirs(restore_subdir, exist_ok=True)

    restore_path = os.path.join(restore_subdir, backup.file_name)

    # Copy backup to restore location
    shutil.copy2(backup.backup_path, restore_path)

    # Verify restored file integrity
    restored_hash = compute_sha256(restore_path)
    integrity_verified = restored_hash == backup.sha256_hash

    # Generate incident ID for recovery tracking
    incident_id = generate_incident_id()

    # Record recovery
    recovery = RecoveryHistory(
        user_id=user_id,
        incident_id=incident_id,
        file_name=backup.file_name,
        original_path=backup.original_path,
        backup_path=backup.backup_path,
        restore_path=restore_path,
        sha256_hash=backup.sha256_hash,
        recovery_date=datetime.utcnow(),
        status="completed" if integrity_verified else "integrity_failed",
        integrity_verified=integrity_verified,
    )
    db.session.add(recovery)
    db.session.commit()

    return {
        "recovery_id": recovery.id,
        "incident_id": incident_id,
        "file_name": backup.file_name,
        "restore_path": restore_path,
        "sha256_hash": backup.sha256_hash,
        "integrity_verified": integrity_verified,
        "recovery_date": recovery.recovery_date.strftime("%Y-%m-%d %H:%M:%S"),
        "status": recovery.status,
    }


def batch_restore(
    backup_ids: List[int],
    user_id: int,
    backup_dir: str,
    restore_dir: str,
) -> Dict:
    """
    Restore multiple files from backup with batch integrity verification.

    Args:
        backup_ids: List of backup record IDs to restore.
        user_id: ID of the user requesting restore.
        backup_dir: Base backup directory.
        restore_dir: Directory to place restored files.

    Returns:
        Dict with overall restore result.
    """
    results = []
    errors = []
    start_time = time.time()

    for bid in backup_ids:
        try:
            result = restore_from_backup(bid, user_id, restore_dir)
            results.append(result)
        except ValueError as e:
            errors.append({"backup_id": bid, "error": str(e)})
        except Exception as e:
            errors.append({"backup_id": bid, "error": f"Unexpected error: {str(e)}"})

    duration = round(time.time() - start_time, 2)
    all_verified = all(r.get("integrity_verified", False) for r in results)

    return {
        "restored_count": len(results),
        "failed_count": len(errors),
        "results": results,
        "errors": errors,
        "all_integrity_verified": all_verified,
        "recovery_duration": duration,
    }


def get_backup_stats(user_id: int) -> Dict:
    """
    Get backup and recovery statistics for a user.

    Returns:
        Dict with dashboard statistics.
    """
    total_backups = BackupHistory.query.filter_by(user_id=user_id, status="active").count()
    total_restored = RecoveryHistory.query.filter_by(user_id=user_id, status="completed").count()
    total_recoveries = RecoveryHistory.query.filter_by(user_id=user_id).count()

    # Threats detected = number of recovery incidents
    threats_detected = RecoveryHistory.query.filter_by(user_id=user_id).count()

    # Recovery success rate
    if total_recoveries > 0:
        recovery_success_rate = round((total_restored / total_recoveries) * 100, 1)
    else:
        recovery_success_rate = 100.0

    # Last backup time
    last_backup = BackupHistory.query.filter_by(
        user_id=user_id, status="active"
    ).order_by(BackupHistory.backup_date.desc()).first()

    last_backup_time = (
        last_backup.backup_date.strftime("%Y-%m-%d %H:%M:%S")
        if last_backup
        else "No backups yet"
    )

    # Protection status
    protection_status = "Active" if total_backups > 0 else "Inactive"

    return {
        "protected_files": total_backups,
        "backups_created": total_backups,
        "files_restored": total_restored,
        "threats_detected": threats_detected,
        "recovery_success_rate": recovery_success_rate,
        "last_backup_time": last_backup_time,
        "protection_status": protection_status,
    }

