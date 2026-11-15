from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

SIZE = 256
BLUE = (45, 120, 230, 255)
WHITE = (255, 255, 255, 255)


def main() -> None:
    output = Path(__file__).resolve().parents[1] / "assets" / "screen_translator.ico"
    output.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((16, 16, 240, 240), radius=54, fill=BLUE)
    font_path = Path("C:/Windows/Fonts/arialbd.ttf")
    font = ImageFont.truetype(str(font_path), 128)
    bounds = draw.textbbox((0, 0), "T", font=font)
    width = bounds[2] - bounds[0]
    height = bounds[3] - bounds[1]
    draw.text(
        ((SIZE - width) / 2, (SIZE - height) / 2 - bounds[1] - 3),
        "T",
        font=font,
        fill=WHITE,
    )
    image.save(output, sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (256, 256)])
    image.save(output.with_suffix(".png"))


if __name__ == "__main__":
    main()
