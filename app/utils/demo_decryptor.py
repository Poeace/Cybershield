"""
Demo Ransomware Decryptor — retrieves the encryption key from SQLite
and decrypts files encrypted by the CyberShield Demo Ransomware Simulator.

This module ONLY decrypts files that were encrypted by our demo simulator.
It does NOT attempt to decrypt unknown or real-world ransomware.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Tuple

from cryptography.fernet import Fernet, InvalidToken

from app.extensions import db
from app.models import EncryptedFile, EncryptionKey
from app.utils.hash_checker import compute_file_sha256


@dataclass
class DecryptionResult:
    """Detailed result of a decryption attempt."""
    success: bool
    original_filename: str = ""
    original_extension: str = ""
    file_size: int = 0
    decryption_timestamp: str = ""
    recovery_status: str = ""
    recovered_path: str = ""
    download_url: str = ""
    open_url: str = ""

    # Error details
    error_category: str = ""  # unknown_family / missing_key / corrupted_file / unsupported_algorithm / other
    error_message: str = ""
    error_details: str = ""


def _categorize_decryption_error(error: Exception) -> Tuple[str, str, str]:
    """
    Categorize a decryption error into a human-readable category.

    Returns:
        Tuple of (error_category, error_message, error_details)
    """
    error_str = str(error).lower()

    if isinstance(error, InvalidToken) or "invalid token" in error_str or "corrupted" in error_str:
        return (
            "corrupted_file",
            "Corrupted Encrypted File",
            "The encrypted file appears to be corrupted or has been modified since encryption. "
            "The decryption integrity check failed, which means the file data cannot be safely recovered. "
            "This can happen if the file was partially overwritten, truncated, or tampered with."
        )

    if "key not found" in error_str or "not found in database" in error_str:
        return (
            "missing_key",
            "Incorrect or Missing Decryption Key",
            "The encryption key required to decrypt this file could not be found in the database. "
            "This may occur if the database was reset, the key record was deleted, "
            "or the file was encrypted outside of this system."
        )

    if "not encrypted by" in error_str or "not available" in error_str or "was not encrypted" in error_str:
        return (
            "unknown_family",
            "Unknown Ransomware Family",
            "This file does not match any records in the CyberShield Demo Ransomware database. "
            "It may have been encrypted by a different ransomware variant, "
            "or it may not be encrypted at all. Decryption is only available for files "
            "encrypted by the CyberShield Demo Ransomware Simulator."
        )

    if "fernet" in error_str or "algorithm" in error_str or "cipher" in error_str:
        return (
            "unsupported_algorithm",
            "Unsupported Encryption Algorithm",
            "The encryption algorithm used on this file is not supported by CyberShield. "
            "Only Fernet (AES-128-CBC with HMAC-SHA256) encrypted files from the "
            "CyberShield Demo Ransomware Simulator can be decrypted."
        )

    # Default / unknown error
    return (
        "other",
        f"Decryption Error: {str(error)}",
        f"An unexpected error occurred during decryption: {str(error)}. "
        "Please try again or contact support if the issue persists."
    )


def decrypt_file(encrypted_path: str, recovery_dir: str) -> Tuple[str, str]:
    """
    Decrypt a file that was encrypted by the Demo Ransomware Simulator.

    Args:
        encrypted_path: Path to the encrypted (.locked) file.
        recovery_dir: Directory where the decrypted file will be saved.

    Returns:
        Tuple of (recovered_filepath, original_filename).

    Raises:
        ValueError: If the file was not encrypted by the demo simulator
                    or the decryption key cannot be found.
    """
    result = decrypt_file_with_details(encrypted_path, recovery_dir)
    if not result.success:
        raise ValueError(result.error_message)
    return result.recovered_path, result.original_filename


def decrypt_file_with_details(
    encrypted_path: str,
    recovery_dir: str,
    scan_id: Optional[int] = None,
    request=None,
) -> DecryptionResult:
    """
    Decrypt a file and return detailed result with categorized errors.

    Args:
        encrypted_path: Path to the encrypted (.locked) file.
        recovery_dir: Directory where the decrypted file will be saved.
        scan_id: Optional scan history ID to update in DB.
        request: Flask request context for URL generation.

    Returns:
        DecryptionResult with success status and full details.
    """
    # Validate path traversal
    if not os.path.isfile(encrypted_path):
        return DecryptionResult(
            success=False,
            error_category="corrupted_file",
            error_message="Encrypted file not found",
            error_details=f"The encrypted file at '{encrypted_path}' does not exist on the server. "
                          "It may have been deleted or moved. Please re-upload the file and try again."
        )

    # Compute hash of the encrypted file
    encrypted_hash = compute_file_sha256(encrypted_path)

    # Create recovered directory with "Recovered Files" subfolder
    recovered_files_dir = os.path.join(recovery_dir, "Recovered Files")
    os.makedirs(recovered_files_dir, exist_ok=True)

    # Look up the key in the database
    encrypted_record = EncryptedFile.query.filter_by(
        encrypted_hash=encrypted_hash
    ).first()

    if not encrypted_record:
        return DecryptionResult(
            success=False,
            error_category="unknown_family",
            error_message="This file was not encrypted by the CyberShield Demo Ransomware Simulator",
            error_details="The file's hash does not match any records in the CyberShield encrypted file database. "
                          "CyberShield can only decrypt files that were encrypted using the "
                          "'Demo Ransomware Simulator' feature within this application. "
                          "If this file was encrypted by real ransomware, please follow the security "
                          "recommendations below."
        )

    # Retrieve the encryption key
    key_record = EncryptionKey.query.get(encrypted_record.encryption_key_id)
    if not key_record:
        return DecryptionResult(
            success=False,
            error_category="missing_key",
            error_message="Encryption key not found in database",
            error_details="The encryption key required to decrypt this file is missing from the database. "
                          "This may happen if the database was cleared or migrated. "
                          "Unfortunately, without the original encryption key, the file cannot be decrypted."
        )

    try:
        key = key_record.key_bytes.encode("utf-8")
        cipher = Fernet(key)

        with open(encrypted_path, "rb") as f:
            encrypted_data = f.read()

        decrypted_data = cipher.decrypt(encrypted_data)

    except InvalidToken:
        return DecryptionResult(
            success=False,
            error_category="corrupted_file",
            error_message="Decryption failed: corrupted file or invalid key",
            error_details="The file could not be decrypted because the decryption integrity check failed. "
                          "This usually means the file has been corrupted, truncated, or modified "
                          "after encryption. If you have a backup of the original encrypted file, "
                          "try uploading it again."
        )
    except Exception as e:
        cat, msg, details = _categorize_decryption_error(e)
        return DecryptionResult(
            success=False,
            error_category=cat,
            error_message=msg,
            error_details=details
        )

    # Save decrypted file in "Recovered Files" folder with original name
    original_name = encrypted_record.original_filename
    recovered_path = os.path.join(recovered_files_dir, original_name)

    with open(recovered_path, "wb") as f:
        f.write(decrypted_data)

    # Get file size
    file_size = os.path.getsize(recovered_path)
    now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    # Update the EncryptedFile record
    encrypted_record.status = "recovered"
    encrypted_record.recovery_timestamp = datetime.utcnow()
    db.session.commit()

    # Build URLs for download and open
    download_url = ""
    open_url = ""
    if request and scan_id:
        download_url = f"/module/ransomware/download/{scan_id}"
        # Check if file type is viewable inline
        ext = os.path.splitext(original_name)[1].lower()
        if ext in (".txt", ".pdf", ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp"):
            open_url = f"/module/ransomware/open/{scan_id}"

    # Get original extension
    original_ext = os.path.splitext(original_name)[1].lower() if original_name else ""

    return DecryptionResult(
        success=True,
        original_filename=original_name,
        original_extension=original_ext,
        file_size=file_size,
        decryption_timestamp=now_str,
        recovery_status="recovered",
        recovered_path=recovered_path,
        download_url=download_url,
        open_url=open_url,
    )

