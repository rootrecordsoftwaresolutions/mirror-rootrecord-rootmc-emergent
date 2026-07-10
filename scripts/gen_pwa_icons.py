"""Generate RootMC PWA icons (192, 512, maskable 512) as PNG.

Design: obsidian #050505 background, gold #FFB800 letter "R" and word "ROOTMC".
Maskable variant keeps the mark inside the safe circle (~80% center).
"""
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "frontend" / "public" / "icons"
OUT.mkdir(parents=True, exist_ok=True)

BG = (5, 5, 5)
GOLD = (255, 184, 0)
WHITE = (255, 255, 255)


def _font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    for path in [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def draw(size: int, path: Path, *, maskable: bool = False) -> None:
    img = Image.new("RGBA", (size, size), BG + (255,))
    d = ImageDraw.Draw(img)

    # subtle 1-unit gold border for non-maskable icons (would be cropped on maskable)
    if not maskable:
        pad = max(2, size // 32)
        radius = size // 6
        d.rounded_rectangle(
            (pad, pad, size - pad - 1, size - pad - 1),
            radius=radius,
            outline=GOLD + (128,),
            width=max(1, size // 96),
        )

    # Safe zone: mark occupies inner ~62% (well within Chrome's 80% maskable safe circle).
    inner = int(size * (0.60 if maskable else 0.72))
    letter_size = int(inner * 0.98)
    label_size = max(8, int(inner * 0.11))

    fL = _font(letter_size, bold=True)
    fW = _font(label_size, bold=True)

    # Vertically stack "R" and "ROOTMC" text with the same optical center
    letter = "R"
    label = "ROOTMC"
    lbbox = d.textbbox((0, 0), letter, font=fL)
    wbbox = d.textbbox((0, 0), label, font=fW)

    letter_w = lbbox[2] - lbbox[0]
    letter_h = lbbox[3] - lbbox[1]
    label_w = wbbox[2] - wbbox[0]
    label_h = wbbox[3] - wbbox[1]

    gap = max(4, size // 40)
    stack_h = letter_h + gap + label_h
    top = (size - stack_h) // 2 - lbbox[1]

    d.text(((size - letter_w) // 2 - lbbox[0], top), letter, font=fL, fill=GOLD)
    d.text(
        ((size - label_w) // 2 - wbbox[0], top + letter_h + gap - wbbox[1]),
        label,
        font=fW,
        fill=WHITE,
    )

    img.save(path, "PNG", optimize=True)
    print(f"wrote {path} ({size}x{size}{' maskable' if maskable else ''})")


draw(192, OUT / "icon-192.png")
draw(512, OUT / "icon-512.png")
draw(512, OUT / "icon-maskable-512.png", maskable=True)
