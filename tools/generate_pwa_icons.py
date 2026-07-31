"""Generate CyberShield PWA icon placeholders (192x192 and 512x512).

Uses Pillow (already in requirements.txt). Run from the project root:
    python tools/generate_pwa_icons.py
"""

import os
from PIL import Image, ImageDraw


def _shield_points(size: int):
    """Shield polygon normalized on a 0..1 grid, scaled to size."""
    pts = [
        (0.50, 0.08), (0.84, 0.16), (0.84, 0.42),
        (0.84, 0.58), (0.70, 0.66), (0.50, 0.94),
        (0.30, 0.66), (0.16, 0.58), (0.16, 0.42),
        (0.16, 0.16),
    ]
    return [(x * size, y * size) for x, y in pts]


def draw_icon(size: int) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))

    # ---- Rounded square background with vertical gradient ----
    radius = int(size * 0.22)
    bg = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    bdraw = ImageDraw.Draw(bg)
    bdraw.rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=(5, 8, 18, 255))
    for y in range(size):
        t = y / size
        color = (
            int(8 + (16 - 8) * t),
            int(14 + (28 - 14) * t),
            int(34 + (64 - 34) * t),
        )
        bdraw.line([(0, y), (size, y)], fill=color)
    img.paste(bg, (0, 0), bg)
    draw = ImageDraw.Draw(img)

    # ---- Cyan glow behind the shield ----
    cx, cy = size * 0.5, size * 0.52
    glow_r = size * 0.38
    for i in range(30, 0, -1):
        alpha = int(16 * (i / 30))
        r = int(glow_r * (i / 30))
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(39, 215, 255, alpha))

    # ---- Shield body (cyan gradient illusion via highlight) ----
    pts = _shield_points(size)
    draw.polygon(pts, fill=(39, 215, 255, 255))

    # Inner outline
    inner = _shield_points(size * 0.94)
    draw.polygon(inner, outline=(5, 8, 18, 255), width=max(1, int(size * 0.02)))

    # ---- Check mark ----
    lw = max(3, int(size * 0.055))
    draw.line([(size * 0.36, size * 0.50), (size * 0.46, size * 0.62)],
              fill=(5, 8, 18, 255), width=lw)
    draw.line([(size * 0.46, size * 0.62), (size * 0.68, size * 0.36)],
              fill=(5, 8, 18, 255), width=lw)

    return img


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    out_dir = os.path.normpath(os.path.join(here, "..", "static", "pwa", "icons"))
    os.makedirs(out_dir, exist_ok=True)

    for s in (192, 512):
        icon = draw_icon(s)
        path = os.path.join(out_dir, f"icon-{s}.png")
        icon.save(path, "PNG")
        print(f"Saved {path} ({s}x{s})")


if __name__ == "__main__":
    main()

