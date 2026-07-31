"""
Incident Report Generator — generates professional PDF incident reports
for the CyberShield Backup & Ransomware Recovery module.

Uses fpdf2 library to create structured PDF documents with:
- Incident identification
- User and file details
- Recovery timeline
- SHA-256 integrity verification
- Professional formatting

Also provides functions to save reports to disk persistently
in the reports/ directory.
"""

from __future__ import annotations

import io
import os
import json
from datetime import datetime
from typing import Dict, List, Optional

from fpdf import FPDF


class IncidentReportPDF(FPDF):
    """Custom PDF class with header/footer for incident reports."""

    def header(self):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(39, 215, 255)  # CyberShield neon blue
        self.cell(0, 8, "CyberShield - Incident Report", align="L")
        self.ln(4)
        self.set_draw_color(39, 215, 255)
        self.set_line_width(0.5)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(6)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(128)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")


def generate_incident_report(incident_data: Dict) -> bytes:
    """
    Generate a professional PDF incident report.

    Args:
        incident_data: Dict containing incident details:
            - incident_id: Unique incident identifier
            - date_time: Date and time of incident
            - user_name: Name of the affected user
            - files_protected: Number of files protected by backup
            - files_encrypted: Number of files encrypted
            - files_restored: Number of files restored
            - threat_level: Threat level (High/Medium/Low)
            - recovery_status: Status of recovery
            - integrity_status: Integrity verification status
            - sha256_verification: Whether SHA-256 was verified
            - recovery_duration: Time taken for recovery

    Returns:
        PDF document as bytes
    """
    pdf = IncidentReportPDF()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    # Title
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(255, 77, 109)  # Danger red
    pdf.cell(0, 12, "INCIDENT REPORT", align="C")
    pdf.ln(4)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(233, 242, 255)
    pdf.cell(0, 6, "Ransomware Attack - Recovery Report", align="C")
    pdf.ln(10)

    # ---- Incident Details Section ----
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(39, 215, 255)
    pdf.cell(0, 8, "1. Incident Details", align="L")
    pdf.ln(2)
    pdf.set_draw_color(39, 215, 255)
    pdf.set_line_width(0.3)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)

    details = [
        ("Incident ID", incident_data.get("incident_id", "N/A")),
        ("Date & Time", incident_data.get("date_time", datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"))),
        ("User Name", incident_data.get("user_name", "Unknown")),
        ("Threat Level", incident_data.get("threat_level", "High")),
        ("Recovery Status", incident_data.get("recovery_status", "Completed")),
    ]

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(233, 242, 255)
    for label, value in details:
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(60, 7, f"{label}:", align="L")
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 7, str(value), align="L")
        pdf.ln()

    pdf.ln(6)

    # ---- Recovery Summary Section ----
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(46, 229, 157)  # Safe green
    pdf.cell(0, 8, "2. Recovery Summary", align="L")
    pdf.ln(2)
    pdf.set_draw_color(46, 229, 157)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)

    summary = [
        ("Files Protected", str(incident_data.get("files_protected", 0))),
        ("Files Encrypted", str(incident_data.get("files_encrypted", 0))),
        ("Files Restored", str(incident_data.get("files_restored", 0))),
        ("Recovery Duration", f"{incident_data.get('recovery_duration', 'N/A')} seconds"),
    ]

    pdf.set_text_color(233, 242, 255)
    for label, value in summary:
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(60, 7, f"{label}:", align="L")
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 7, value, align="L")
        pdf.ln()

    pdf.ln(6)

    # ---- Integrity Verification Section ----
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(255, 209, 102)  # Warning yellow
    pdf.cell(0, 8, "3. File Integrity Verification", align="L")
    pdf.ln(2)
    pdf.set_draw_color(255, 209, 102)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)

    integrity = incident_data.get("integrity_status", "Verification Completed")
    sha256_status = incident_data.get("sha256_verification", "Verified")

    pdf.set_text_color(233, 242, 255)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(60, 7, "Integrity Status:", align="L")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(46, 229, 157 if integrity == "Verified" else 255, 77, 109)
    pdf.cell(0, 7, integrity, align="L")
    pdf.ln()

    pdf.set_text_color(233, 242, 255)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(60, 7, "SHA-256 Verification:", align="L")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(46, 229, 157 if sha256_status == "Verified" else 255, 77, 109)
    pdf.cell(0, 7, sha256_status, align="L")
    pdf.ln()

    pdf.ln(6)

    # ---- Affected Files Section ----
    affected_files = incident_data.get("affected_files", [])
    if affected_files:
        pdf.set_font("Helvetica", "B", 13)
        pdf.set_text_color(255, 77, 109)
        pdf.cell(0, 8, "4. Affected Files", align="L")
        pdf.ln(2)
        pdf.set_draw_color(255, 77, 109)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(4)

        # Table header
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_fill_color(10, 18, 35)
        pdf.set_text_color(39, 215, 255)
        col_widths = [10, 70, 50, 50]
        headers = ["#", "File Name", "Encrypted Name", "Status"]
        for i, h in enumerate(headers):
            pdf.cell(col_widths[i], 7, h, border=1, align="C", fill=True)
        pdf.ln()

        # Table rows
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(233, 242, 255)
        for idx, af in enumerate(affected_files[:15], 1):  # Max 15 files
            pdf.cell(col_widths[0], 6, str(idx), border=1, align="C")
            pdf.cell(col_widths[1], 6, af.get("file_name", "Unknown"), border=1)
            pdf.cell(col_widths[2], 6, af.get("encrypted_name", "Unknown"), border=1)
            pdf.cell(col_widths[3], 6, "Restored", border=1, align="C")
            pdf.ln()

        if len(affected_files) > 15:
            pdf.set_font("Helvetica", "I", 8)
            pdf.cell(0, 6, f"... and {len(affected_files) - 15} more files", align="L")
            pdf.ln()

        pdf.ln(4)

    # ---- Recovery Timeline Section ----
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(39, 215, 255)
    pdf.cell(0, 8, "5. Recovery Timeline", align="L")
    pdf.ln(2)
    pdf.set_draw_color(39, 215, 255)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)

    timeline = incident_data.get("timeline", [
        "Backup Created",
        "Ransomware Attack",
        "Attack Detected",
        "Recovery Started",
        "Recovery Completed",
    ])

    pdf.set_text_color(233, 242, 255)
    for step in timeline:
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(5, 7, chr(8226), align="C")  # bullet point
        pdf.cell(0, 7, step, align="L")
        pdf.ln()

    pdf.ln(6)

    # ---- Footer Note ----
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(128)
    pdf.cell(0, 5, "This report was automatically generated by CyberShield Backup & Ransomware Recovery Module.", align="C")
    pdf.ln()
    pdf.cell(0, 5, "CyberShield v1.0 | MCA Major Project", align="C")

    # Return PDF as bytes
    return pdf.output(dest="S").encode("latin-1")


# =============================================================================
# REPORT SAVING & PERSISTENCE
# =============================================================================


def save_incident_report(
    pdf_bytes: bytes,
    incident_id: str,
    reports_dir: str,
    metadata: Optional[Dict] = None,
) -> str:
    """
    Save a generated incident report PDF to disk persistently.

    Creates a subdirectory structure: reports/report_{incident_id}/
    and stores the PDF file along with a JSON metadata file.

    Args:
        pdf_bytes: The PDF document as bytes.
        incident_id: Unique incident identifier (used for folder naming).
        reports_dir: Base directory for storing reports.
        metadata: Optional dict of metadata to save alongside the PDF.

    Returns:
        Path to the saved PDF file.

    Raises:
        IOError: If the file cannot be written.
    """
    # Create sanitized folder name from incident_id
    safe_id = "".join(c if c.isalnum() or c in "_-" else "_" for c in incident_id)
    report_subdir = os.path.join(reports_dir, f"report_{safe_id}")
    os.makedirs(report_subdir, exist_ok=True)

    # Save PDF file
    pdf_filename = f"incident_report_{safe_id}.pdf"
    pdf_path = os.path.join(report_subdir, pdf_filename)
    with open(pdf_path, "wb") as f:
        f.write(pdf_bytes)

    # Save metadata JSON if provided
    if metadata:
        meta_path = os.path.join(report_subdir, f"metadata_{safe_id}.json")
        with open(meta_path, "w") as f:
            json.dump(metadata, f, indent=2, default=str)

    return pdf_path


def get_user_reports(user_id: int, reports_dir: str) -> List[Dict]:
    """
    List all saved report directories in the reports folder.

    Scans the reports/ directory for report_{incident_id} subdirectories
    and reads any metadata JSON files found within.

    Args:
        user_id: ID of the user (used for filtering if metadata has user_id).
        reports_dir: Base directory for stored reports.

    Returns:
        List of dicts with report metadata, sorted by date descending.
    """
    if not os.path.exists(reports_dir):
        return []

    reports = []
    for item in os.listdir(reports_dir):
        item_path = os.path.join(reports_dir, item)
        if not os.path.isdir(item_path) or not item.startswith("report_"):
            continue

        # Look for PDF and metadata files
        pdf_file = None
        metadata = {}

        for fname in os.listdir(item_path):
            fpath = os.path.join(item_path, fname)
            if fname.endswith(".pdf"):
                pdf_file = fpath
            elif fname.endswith(".json"):
                try:
                    with open(fpath, "r") as f:
                        metadata = json.load(f)
                except (json.JSONDecodeError, IOError):
                    pass

        # Filter by user_id if metadata has it
        if metadata.get("user_id") and metadata["user_id"] != user_id:
            continue

        reports.append({
            "incident_id": item.replace("report_", ""),
            "pdf_path": pdf_file,
            "metadata": metadata,
            "report_date": metadata.get("date_time", "Unknown"),
            "created_at": datetime.fromtimestamp(
                os.path.getctime(item_path)
            ).strftime("%Y-%m-%d %H:%M:%S"),
        })

    # Sort by creation time descending
    reports.sort(key=lambda r: r["created_at"], reverse=True)
    return reports

