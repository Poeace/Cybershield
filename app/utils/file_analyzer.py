"""
File Analyzer — orchestrates the full ransomware analysis pipeline.

Scans an uploaded file for:
- Magic bytes (file signature)
- File extensions (including double extensions)
- Known ransomware extensions
- SHA-256 hash
- Shannon entropy
- Demo simulator match
"""

from __future__ import annotations

import os
import struct
from dataclasses import dataclass, field
from typing import Optional, Tuple

from app.utils.entropy_checker import calculate_file_entropy
from app.utils.hash_checker import compute_file_sha256


# Known ransomware extensions (sample — expand as needed)
KNOWN_RANSOMWARE_EXTENSIONS: Tuple[str, ...] = (
    ".locked",
    ".encrypted",
    ".lockbit",
    ".wcry",
    ".crypt",
    ".zepto",
    ".locky",
    ".dharma",
    ".cry",
    ".r5a",
    ".wallet",
    ".petya",
    ".notpetya",
    ".badger",
    ".gandcrab",
    ".revil",
    ".conti",
    ".blackbasta",
    ".akira",
    ".cryptolocker",
    ".wannacry",
    ".cerber",
    ".teslacrypt",
    ".satan",
    ".leather",
    ".crypton",
    ".encrypt",
    ".crypted",
    ".enc",
    ".lockedfile",
    ".hive",
    ".blackcat",
    ".lockbit3",
    ".lilocked",
    ".maze",
    ".nemty",
    ".nrw",
    ".onion",
    ".paym",
    ".qewe",
    ".ragnar",
    ".ryuk",
    ".sage",
    ".scorpio",
    ".snake",
    ".stop",
    ".tox",
    ".trinity",
    ".venom",
    ".XXXXXX",
)

# Executable / dangerous extensions
EXECUTABLE_EXTENSIONS: Tuple[str, ...] = (
    ".exe",
    ".msi",
    ".scr",
    ".bat",
    ".cmd",
    ".ps1",
    ".vbs",
    ".js",
    ".jar",
    ".com",
    ".pif",
    ".wsf",
    ".hta",
)

# Common file magic bytes (signatures)
MAGIC_BYTES: dict = {
    b"\x25\x50\x44\x46": "PDF",
    b"\x89\x50\x4E\x47": "PNG Image",
    b"\xFF\xD8\xFF": "JPEG Image",
    b"\x47\x49\x46\x38": "GIF Image",
    b"\x42\x4D": "BMP Image",
    b"\x50\x4B\x03\x04": "ZIP/DOCX/XLSX",
    b"\x52\x61\x72\x21": "RAR Archive",
    b"\x1F\x8B\x08": "GZ Archive",
    b"\x7F\x45\x4C\x46": "ELF Binary",
    b"\x4D\x5A": "PE (Windows Executable)",
    b"\xCA\xFE\xBA\xBE": "Java Class",
    b"\x49\x44\x33": "MP3 Audio",
    b"\x00\x00\x01\x00": "ICO Icon",
    b"\x4F\x67\x67\x53": "OGG Audio",
    b"\x1A\x45\xDF\xA3": "MKV/WebM Video",
    b"\xFE\xED\xFA\xCE": "Mach-O 32-bit",
    b"\xFE\xED\xFA\xCF": "Mach-O 64-bit",
    b"\xCE\xFA\xED\xFE": "Mach-O Reverse 32-bit",
    b"\xCF\xFA\xED\xFE": "Mach-O Reverse 64-bit",
}


@dataclass
class AnalysisResult:
    """Structured analysis result for a scanned file."""

    file_name: str
    original_extension: str
    current_extension: str
    file_size: int
    sha256: str
    entropy: float
    magic_bytes_hex: str
    detected_magic: str
    has_double_extension: bool
    is_executable: bool
    is_known_ransomware_ext: bool
    is_demo_ransomware: bool
    reasons: list[str] = field(default_factory=list)


def get_extension(filepath: str) -> str:
    """Extract the file extension (lowercase)."""
    _, ext = os.path.splitext(filepath)
    return ext.lower()


def has_double_extension(filename: str) -> Tuple[bool, str, str]:
    """
    Check if a filename has a double extension (e.g., invoice.pdf.exe).

    Returns:
        (is_double, first_ext, second_ext)
    """
    parts = filename.lower().split(".")
    if len(parts) >= 3:
        # e.g., file.pdf.exe -> [file, pdf, exe]
        return True, f".{parts[-2]}", f".{parts[-1]}"
    return False, "", ""


def detect_magic_bytes(filepath: str, num_bytes: int = 8) -> Tuple[str, str]:
    """
    Read magic bytes from file and attempt to identify the file type.

    Returns:
        (hex_string, description)
    """
    try:
        with open(filepath, "rb") as f:
            header = f.read(num_bytes)

        hex_str = header.hex(" ").upper()

        # Check against known magic byte signatures
        for magic, desc in MAGIC_BYTES.items():
            if header.startswith(magic):
                return hex_str, desc

        # If unknown, check if all bytes look like encrypted/random data
        if len(header) >= 4:
            # High entropy in header is a strong indicator
            from app.utils.entropy_checker import calculate_entropy

            hdr_entropy = calculate_entropy(header)
            if hdr_entropy > 7.0:
                return hex_str, "Encrypted/Random Data"

        return hex_str, "Unknown"

    except Exception:
        return "", "Cannot read"


def analyze_file(filepath: str, original_filename: str) -> AnalysisResult:
    """
    Run the full analysis pipeline on a file.

    Args:
        filepath: Absolute path to the uploaded file.
        original_filename: Original name of the uploaded file.

    Returns:
        AnalysisResult with all detection fields populated.
    """
    file_size = os.path.getsize(filepath)
    sha256 = compute_file_sha256(filepath)
    entropy = calculate_file_entropy(filepath)
    magic_hex, magic_desc = detect_magic_bytes(filepath)

    current_ext = get_extension(filepath)
    _, first_ext, second_ext = has_double_extension(original_filename)
    double_ext = first_ext != "" and second_ext != ""

    is_known_ransom = current_ext in KNOWN_RANSOMWARE_EXTENSIONS
    is_exec = current_ext in EXECUTABLE_EXTENSIONS or magic_desc == "PE (Windows Executable)"

    # Determine original extension (strip .locked if ransomware)
    original_ext = current_ext
    if current_ext in (".locked", ".encrypted", ".crypt"):
        # If original had a double ext like .pdf.exe, try to recover
        if double_ext:
            original_ext = first_ext
        else:
            original_ext = "(unknown — possibly encrypted)"

    reasons: list[str] = []

    if is_known_ransom:
        reasons.append(f"Known ransomware extension: {current_ext}")
    if is_exec:
        reasons.append(f"Executable extension detected: {current_ext}")
    if double_ext:
        reasons.append(f"Double extension detected: {original_filename} (possible masquerading)")
    if entropy >= 7.5:
        reasons.append(f"Very high file entropy ({entropy:.2f}) — likely encrypted or compressed")
    elif entropy >= 6.5:
        reasons.append(f"High file entropy ({entropy:.2f})")
    if magic_desc == "Encrypted/Random Data":
        reasons.append("File header appears to be encrypted/random")

    # Check against demo ransomware table (done in routes via DB lookup)
    is_demo = False  # Will be set externally after DB lookup
    if magic_desc == "Encrypted/Random Data" and current_ext == ".locked":
        reasons.append("File appears to be encrypted (demo ransomware pattern)")

    return AnalysisResult(
        file_name=original_filename,
        original_extension=original_ext,
        current_extension=current_ext,
        file_size=file_size,
        sha256=sha256,
        entropy=entropy,
        magic_bytes_hex=magic_hex,
        detected_magic=magic_desc,
        has_double_extension=double_ext,
        is_executable=is_exec,
        is_known_ransomware_ext=is_known_ransom,
        is_demo_ransomware=is_demo,
        reasons=reasons,
    )

