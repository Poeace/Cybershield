"""
Ransomware Risk Engine — calculates a risk score (0-100) based on file
analysis features and determines Safe / Medium Risk / High Risk status.

Scoring factors:
- Known ransomware extension (+30)
- Executable extension (+15)
- Double extension (+20)
- Very high entropy >= 7.5 (+25)
- High entropy >= 6.5 (+15)
- Known malicious hash (+20)
- Demo ransomware match (+40, mutually exclusive with known hash)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from app.utils.file_analyzer import AnalysisResult


@dataclass
class RansomwareRiskResult:
    risk_score: int  # 0-100
    status: str  # "Safe", "Medium Risk", "High Risk"
    reasons: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    detection_family: str = ""
    recovery_available: bool = False


def compute_ransomware_risk(
    analysis: AnalysisResult,
    is_demo_ransomware: bool = False,
    is_known_malicious_hash: bool = False,
) -> RansomwareRiskResult:
    """
    Compute a risk score (0-100) for a file based on analysis results.
    """
    score = 0
    reasons: List[str] = list(analysis.reasons)
    detection_family = ""
    recovery_available = False

    # 1. Known ransomware extension (+30)
    if analysis.is_known_ransomware_ext:
        score += 30

    # 2. Executable extension (+15)
    if analysis.is_executable:
        score += 15

    # 3. Double extension (+20)
    if analysis.has_double_extension:
        score += 20

    # 4. Entropy contribution
    if analysis.entropy >= 7.5:
        score += 25
        if "Very high file entropy" not in " ".join(reasons):
            reasons.append(f"Very high entropy ({analysis.entropy:.2f}) — strong encryption indicator")
    elif analysis.entropy >= 6.5:
        score += 15
        if "High file entropy" not in " ".join(reasons):
            reasons.append(f"High entropy ({analysis.entropy:.2f})")

    # 5. Known malicious hash (+20)
    if is_known_malicious_hash:
        score += 20
        reasons.append("File hash matches known malicious database")

    # 6. Demo ransomware match (+40)
    if is_demo_ransomware:
        score += 40
        detection_family = "CyberShield Demo Ransomware"
        recovery_available = True
        reasons.append("File encrypted by CyberShield Demo Ransomware")

    # Cap at 100
    score = min(100, score)

    # Status thresholds
    if score >= 71:
        status = "High Risk"
        recommendations = [
            "Isolate this file immediately — do not open it.",
            "Disconnect the affected system from the network.",
            "Run a full antivirus/anti-malware scan.",
            "Restore from verified backups if possible.",
            "Contact your security team or a cybersecurity professional.",
        ]
        if recovery_available:
            recommendations.insert(0, "Decryption key available — use the Decrypt button below.")
    elif score >= 31:
        status = "Medium Risk"
        recommendations = [
            "Exercise caution with this file.",
            "Scan with an up-to-date security solution.",
            "Verify the file source and integrity.",
            "Do not execute or open if the source is untrusted.",
        ]
    else:
        status = "Safe"
        recommendations = [
            "No significant ransomware indicators detected.",
            "Keep your OS and security software updated.",
            "Always verify file sources before opening.",
        ]

    if not detection_family:
        if analysis.is_known_ransomware_ext or analysis.entropy >= 7.5:
            detection_family = "Unknown (potential ransomware)"
        else:
            detection_family = "N/A (no encryption detected)"

    return RansomwareRiskResult(
        risk_score=score,
        status=status,
        reasons=reasons,
        recommendations=recommendations,
        detection_family=detection_family,
        recovery_available=recovery_available,
    )
