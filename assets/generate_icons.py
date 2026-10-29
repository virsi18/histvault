"""
Generates high-resolution multi-size Windows .ico files.
"""
from PIL import Image, ImageDraw
from pathlib import Path

OUT_DIR = Path(__file__).parent / "icons"
OUT_DIR.mkdir(parents=True, exist_ok=True)
SIZES = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]


def create_shield_icon() -> Image.Image:
    img = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Background rounded squircle (Apple Blue)
    draw.rounded_rectangle([16, 16, 240, 240], radius=52, fill=(10, 132, 255, 255))
    # Inner shield
    shield_pts = [(128, 48), (196, 72), (196, 140), (128, 204), (60, 140), (60, 72)]
    draw.polygon(shield_pts, fill=(255, 255, 255, 240))
    # Inner checkmark in shield
    draw.line([(100, 128), (120, 150), (160, 102)], fill=(10, 132, 255, 255), width=14)
    return img


def create_safari_icon() -> Image.Image:
    img = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Background rounded squircle (Deep Indigo/Dark)
    draw.rounded_rectangle([16, 16, 240, 240], radius=52, fill=(24, 24, 40, 255))
    # Compass dial circle
    draw.ellipse([48, 48, 208, 208], outline=(255, 255, 255, 220), width=6)
    # Red needle top-right
    draw.polygon([(128, 128), (170, 70), (145, 120)], fill=(255, 69, 58, 255))
    # White needle bottom-left
    draw.polygon([(128, 128), (86, 186), (111, 136)], fill=(240, 240, 245, 255))
    # Center pin
    draw.ellipse([122, 122, 134, 134], fill=(255, 255, 255, 255))
    return img


def create_vault_icon() -> Image.Image:
    img = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Background rounded squircle (Dark Titanium)
    draw.rounded_rectangle([16, 16, 240, 240], radius=52, fill=(28, 28, 32, 255))
    # Gold safe dial rim
    draw.ellipse([64, 64, 192, 192], outline=(255, 214, 10, 230), width=10)
    # Inner safe dial
    draw.ellipse([88, 88, 168, 168], fill=(44, 44, 48, 255), outline=(255, 214, 10, 180), width=4)
    # Dial knob
    draw.ellipse([116, 116, 140, 140], fill=(255, 214, 10, 255))
    # Dial notches
    draw.line([(128, 64), (128, 76)], fill=(255, 214, 10, 255), width=4)
    draw.line([(128, 180), (128, 192)], fill=(255, 214, 10, 255), width=4)
    draw.line([(64, 128), (76, 128)], fill=(255, 214, 10, 255), width=4)
    draw.line([(180, 128), (192, 128)], fill=(255, 214, 10, 255), width=4)
    return img


def create_clock_icon() -> Image.Image:
    img = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Background rounded squircle (Graphite)
    draw.rounded_rectangle([16, 16, 240, 240], radius=52, fill=(38, 38, 42, 255))
    # Clock face ring
    draw.ellipse([52, 52, 204, 204], outline=(245, 245, 247, 220), width=8)
    # Hour hand (pointing to 10)
    draw.line([(128, 128), (88, 92)], fill=(255, 255, 255, 255), width=8)
    # Minute hand (pointing to 2)
    draw.line([(128, 128), (174, 82)], fill=(255, 69, 58, 255), width=6)
    # Center dot
    draw.ellipse([122, 122, 134, 134], fill=(255, 255, 255, 255))
    return img


def create_stealth_icon() -> Image.Image:
    img = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Background rounded squircle (Matte Black)
    draw.rounded_rectangle([16, 16, 240, 240], radius=52, fill=(18, 18, 20, 255))
    # Hat / Visor
    draw.polygon([(64, 98), (192, 98), (170, 68), (86, 68)], fill=(142, 142, 147, 255))
    draw.ellipse([48, 92, 208, 108], fill=(174, 174, 178, 255))
    # Sunglasses lenses
    draw.rounded_rectangle([68, 126, 118, 164], radius=14, fill=(48, 209, 88, 240))
    draw.rounded_rectangle([138, 126, 188, 164], radius=14, fill=(48, 209, 88, 240))
    # Bridge
    draw.line([(118, 138), (138, 138)], fill=(142, 142, 147, 255), width=5)
    return img


def main():
    icons = {
        "shield.ico": create_shield_icon(),
        "safari.ico": create_safari_icon(),
        "vault.ico": create_vault_icon(),
        "clock.ico": create_clock_icon(),
        "stealth.ico": create_stealth_icon(),
    }

    for name, img in icons.items():
        out_path = OUT_DIR / name
        img.save(out_path, format="ICO", sizes=SIZES)
        print(f"Generated {out_path.name} ({out_path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
