from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class QRDecodeResult:
    payload: str
    upi_handle: Optional[str] = None


def _extract_pa_parameter(payload: str) -> Optional[str]:
    """Extract UPI handle from QR payload.

    Typical UPI QR payload example:
      "upi://pay?pa=some@okaxis&pn=Name&am=10"
    """
    if not payload:
        return None

    # Robust pa extraction without depending on urllib variations
    # - allow pa=... until & or end of string
    lower = payload.lower()

    key = "pa="
    idx = lower.find(key)
    if idx == -1:
        return None

    start = idx + len(key)
    end = lower.find("&", start)
    if end == -1:
        end = len(payload)

    return payload[start:end].strip()


def decode_qr_upi_handle(image_bytes: bytes) -> QRDecodeResult:
    """Decode a QR image and extract UPI handle from the QR payload.

    This function uses optional dependencies.
    If QR decoding libraries are not installed, it raises a RuntimeError.
    """

    # Try pyzbar + Pillow (common pure-Python QR decode approach)
    try:
        from PIL import Image  # type: ignore
        from pyzbar.pyzbar import decode as qr_decode  # type: ignore
        import io

        image = Image.open(io.BytesIO(image_bytes))
        codes = qr_decode(image)
        if not codes:
            raise RuntimeError("No QR code detected in the uploaded image.")

        # Take the first QR payload
        payload = (codes[0].data or b"").decode("utf-8", errors="ignore")
        upi_handle = _extract_pa_parameter(payload)
        return QRDecodeResult(payload=payload, upi_handle=upi_handle)

    except ModuleNotFoundError:
        # Dependencies not installed.
        raise RuntimeError(
            "QR decoding is not available on this server (missing QR decoding libraries). "
            "Please paste the UPI ID manually."
        )

