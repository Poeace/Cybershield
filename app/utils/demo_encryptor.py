"""
Demo Ransomware Simulator — encrypts a file using Fernet (AES) and
stores the key securely in SQLite. FOR DEMONSTRATION AND TESTING ONLY.

This is NOT malicious software. It is an educational tool for
cybersecurity awareness and training within CyberShield.
"""

from __future__ import annotations

import os
import shutil
from datetime import datetime
from typing import Tuple

from cryptography.fernet import Fernet

from app.extensions import db
from app.models import EncryptedFile, EncryptionKey
from app.utils.hash_checker import compute_file_sha256, register_malicious_hash


def encrypt_file(source_path: str, upload_dir: str) -> Tuple[str, str, str, str]:
    """
    Encrypt a file using Fernet symmetric encryption.

    Steps:
    1. Generate a Fernet key.
    2. Read the source file.
    3. Encrypt the file data.
    4. Write encrypted data to a new file with .locked extension.
    5. Compute SHA-256 of original and encrypted files.
    6. Store the encryption key and metadata in SQLite.

    Args:
        source_path: Path to the source file to encrypt.
        upload_dir: Directory to store the encrypted output.

    Returns:
        Tuple of (encrypted_filepath, key_string, sha256_original, sha256_encrypted)
    """
    if not os.path.isfile(source_path):
        raise FileNotFoundError(f"Source file not found: {source_path}")

    # Generate Fernet key
    key = Fernet.generate_key()
    cipher = Fernet(key)

    # Read and encrypt
    with open(source_path, "rb") as f:
        original_data = f.read()

    encrypted_data = cipher.encrypt(original_data)

    # Compute hashes
    sha256_original = compute_file_sha256(source_path)
    sha256_encrypted = compute_file_sha256(source_path)  # placeholder, will recompute

    # Write encrypted file
    original_name = os.path.basename(source_path)
    encrypted_filename = f"{original_name}.locked"
    encrypted_path = os.path.join(upload_dir, encrypted_filename)

    with open(encrypted_path, "wb") as f:
        f.write(encrypted_data)

    # Recompute hash of encrypted file
    sha256_encrypted = compute_file_sha256(encrypted_path)

    # Register hash as known malicious (for detection)
    register_malicious_hash(sha256_encrypted)

    # Store encryption key in DB
    key_record = EncryptionKey(
        file_hash=sha256_encrypted,
        key_bytes=key.decode("utf-8"),
        created_at=datetime.utcnow(),
    )
    db.session.add(key_record)

    # Store encrypted file record
    encrypted_record = EncryptedFile(
        original_filename=original_name,
        encrypted_filename=encrypted_filename,
        original_hash=sha256_original,
        encrypted_hash=sha256_encrypted,
        encryption_key_id=key_record.id,
        encryption_timestamp=datetime.utcnow(),
        status="encrypted",
    )
    db.session.add(encrypted_record)
    db.session.commit()

    return encrypted_path, key.decode("utf-8"), sha256_original, sha256_encrypted


def generate_key_only() -> str:
    """
    Generate a Fernet key without encrypting any file.

    Returns:
        Fernet key as a string.
    """
    return Fernet.generate_key().decode("utf-8")

