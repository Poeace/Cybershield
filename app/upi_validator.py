from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable


# Typical UPI handle format: name@bank (e.g., abc@okaxis)
# - local-part: 2-64 chars, letters/digits and common separators . _ -
# - handle (provider id): 2-32 chars, letters/digits and common separators
UPI_REGEX = re.compile(r"^(?P<local>[a-z0-9]{2,64}(?:[\._\-]?[a-z0-9]+)*)@(?P<provider>[a-z0-9]{2,32}(?:[\._\-]?[a-z0-9]+)*)$")


# Minimal allowlist per requirement examples.
# Providers are matched case-insensitively.
KNOWN_PROVIDERS: set[str] = {
    "ybl",
    "okaxis",
    "paytm",
    "apl",
    "ibl",
    # common ones (safe to keep the list extendable)
    "hdfcbank",
    "icici",
    "axis",
    "sbi",
    "sbin",
    "kotak",
    "indusind",
    "idbi",
    "jkb",
    "barodabank",
    "boi",
    "citi",
    "yesbank",
    "idfc",
    "rbl",
}


@dataclass(frozen=True)
class UpiValidationResult:
    is_valid: bool
    upi_handle: str
    provider: str | None
    reasons: tuple[str, ...]


def validate_upi_handle(upi_handle: str, known_providers: Iterable[str] = KNOWN_PROVIDERS) -> UpiValidationResult:
    normalized = (upi_handle or "").strip().lower()

    if not normalized:
        return UpiValidationResult(
            is_valid=False,
            upi_handle="",
            provider=None,
            reasons=("UPI handle is empty.",),
        )

    m = UPI_REGEX.match(normalized)
    if not m:
        return UpiValidationResult(
            is_valid=False,
            upi_handle=normalized,
            provider=None,
            reasons=("UPI ID format is invalid. Expected: name@provider (e.g., abc@okaxis).",),
        )

    provider = m.group("provider")
    reasons: list[str] = []

    if provider not in set(p.lower() for p in known_providers):
        reasons.append(f"Unknown UPI provider: '{provider}'.")
        return UpiValidationResult(
            is_valid=False,
            upi_handle=normalized,
            provider=provider,
            reasons=tuple(reasons),
        )

    return UpiValidationResult(
        is_valid=True,
        upi_handle=normalized,
        provider=provider,
        reasons=tuple(),
    )

