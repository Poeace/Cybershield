from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from app.upi_validator import validate_upi_handle


@dataclass(frozen=True)
class RiskResult:
    risk_score: int  # 0-100
    status: str  # Safe/Medium/High
    reasons: tuple[str, ...]
    recommendations: tuple[str, ...]
    payment_recommendation: str = ""


def compute_risk_score(upi_handle: str, report_count: int, known_providers: Iterable[str] | None = None) -> RiskResult:
    """Compute risk score based on:
    - invalid UPI format
    - unknown provider
    - previous user reports

    Scoring is intentionally transparent and deterministic.
    """

    reasons: list[str] = []
    score = 0

    known = set((p.lower() for p in (known_providers or [])))

    validation = validate_upi_handle(upi_handle, known_providers=known if known else None)  # type: ignore[arg-type]

    if not validation.is_valid:
        # invalid format / unknown provider
        # If provider is unknown, validation may return is_valid=False.
        for r in validation.reasons:
            reasons.append(r)
        if any("format is invalid" in r.lower() for r in validation.reasons):
            score += 45
        else:
            # likely unknown provider
            score += 35

    # Report count contribution
    # 0 -> 0 points, 1 -> 20, 2 -> 35, 3+ -> 55 (cap at 60 total contribution)
    rc = max(0, int(report_count or 0))
    if rc == 1:
        score += 20
        reasons.append("This UPI has been reported by 1 user as potentially fraudulent.")
    elif rc == 2:
        score += 35
        reasons.append("This UPI has been reported by 2 users as potentially fraudulent.")
    elif rc >= 3:
        score += 55
        reasons.append(f"This UPI has been reported by {rc} users as potentially fraudulent.")

    # Normalize/cap
    score = max(0, min(100, score))

    # Status thresholds
    if score >= 75:
        status = "High Risk"
        recommendations = (
            "Do not proceed with the payment.",
            "Verify the recipient using an official contact/known channel.",
            "Report suspicious UPI activity to your bank/app support.",
        )
    elif score >= 35:
        status = "Medium Risk"
        recommendations = (
            "Proceed only if you trust the recipient.",
            "Double-check the UPI ID (payee handle) before confirming.",
            "If anything looks off, cancel and use an alternative payment method.",
        )
    else:
        status = "Safe"
        recommendations = (
            "No strong fraud indicators found for this scan.",
            "Still verify the UPI ID and payment details before you authorize.",
        )

    if not reasons:
        reasons = ("No major indicators detected.",)

    # Payment recommendation (clear go/no-go for the user)
    if score >= 75:
        payment_recommendation = "❌ Do Not Pay – This UPI ID appears risky. Avoid making any payment."
    elif score >= 35:
        payment_recommendation = "⚠️ Pay with Caution – Verify recipient details and confirm the UPI ID before sending money."
    else:
        payment_recommendation = "✅ Safe to Pay – No strong fraud indicators detected for this UPI ID."

    # Round score within 0-100
    return RiskResult(
        risk_score=int(score),
        status=status,
        reasons=tuple(reasons),
        recommendations=tuple(recommendations),
        payment_recommendation=payment_recommendation,
    )

