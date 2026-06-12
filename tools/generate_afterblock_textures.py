from pathlib import Path
from PIL import Image, ImageDraw


OBJECT_LIBRARY = [
    ("book", (108, 46, 39)),
    ("earbuds", (232, 235, 232)),
    ("monitor", (32, 36, 46)),
    ("school_bag", (85, 99, 138)),
    ("painting", (176, 63, 48)),
    ("water_bottle", (48, 132, 190)),
    ("lamp", (222, 177, 82)),
    ("microphone", (42, 42, 48)),
    ("tissue", (226, 226, 216)),
    ("keyboard", (182, 186, 184)),
    ("charger", (225, 224, 214)),
    ("mug", (196, 82, 74)),
    ("shoes", (92, 78, 70)),
    ("key", (219, 174, 76)),
    ("toy_car", (205, 42, 38)),
    ("notebook", (68, 119, 168)),
    ("glasses", (38, 38, 42)),
    ("wallet", (96, 59, 35)),
    ("usb_drive", (166, 169, 172)),
    ("clock", (218, 218, 204)),
]


def px(draw, box, fill):
    scale = 4
    x1, y1, x2, y2 = box
    draw.rectangle([x1 * scale, y1 * scale, (x2 + 1) * scale - 1, (y2 + 1) * scale - 1], fill=fill)


def draw_icon(kind, color, variant):
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    shade = tuple(max(0, c - 42) for c in color)
    light = tuple(min(255, c + 38) for c in color)
    dark = (32, 28, 25)

    if kind == "book":
        px(d, (7, 4, 12, 13), color); px(d, (4, 4, 6, 13), shade); px(d, (8, 6, 11, 7), light)
    elif kind == "earbuds":
        px(d, (5, 5, 7, 7), color); px(d, (10, 5, 12, 7), color); px(d, (7, 8, 7, 13), light); px(d, (10, 8, 10, 13), light)
    elif kind == "monitor":
        px(d, (3, 4, 13, 10), dark); px(d, (4, 5, 12, 9), color); px(d, (7, 11, 9, 12), shade); px(d, (5, 13, 11, 13), shade)
    elif kind == "school_bag":
        px(d, (4, 6, 12, 14), color); px(d, (6, 4, 10, 5), shade); px(d, (5, 8, 11, 9), light)
    elif kind == "painting":
        px(d, (3, 3, 13, 13), (94, 61, 39)); px(d, (4, 4, 12, 12), color); px(d, (7, 5, 10, 8), light)
    elif kind == "water_bottle":
        px(d, (6, 3, 10, 4), light); px(d, (5, 5, 11, 14), color); px(d, (6, 7, 10, 8), (210, 238, 245))
    elif kind == "lamp":
        px(d, (5, 3, 11, 7), light); px(d, (7, 8, 9, 13), shade); px(d, (5, 14, 11, 14), color)
    elif kind == "microphone":
        px(d, (6, 3, 10, 9), dark); px(d, (7, 4, 9, 8), color); px(d, (8, 10, 8, 13), shade); px(d, (5, 14, 11, 14), shade)
    elif kind == "tissue":
        px(d, (4, 7, 12, 13), color); px(d, (6, 4, 10, 7), light); px(d, (5, 9, 11, 10), (180, 200, 220))
    elif kind == "keyboard":
        px(d, (2, 7, 14, 12), color)
        for x in range(3, 14, 2): px(d, (x, 8, x, 8), dark)
        for x in range(4, 13, 2): px(d, (x, 10, x, 10), dark)
    elif kind == "charger":
        px(d, (4, 5, 8, 9), color); px(d, (9, 6, 12, 8), light); px(d, (12, 7, 14, 7), shade)
    elif kind == "mug":
        px(d, (4, 5, 10, 13), color); px(d, (10, 7, 13, 10), shade); px(d, (5, 4, 9, 4), light)
    elif kind == "shoes":
        px(d, (3, 9, 8, 12), color); px(d, (9, 8, 14, 12), shade); px(d, (4, 12, 14, 13), dark)
    elif kind == "key":
        px(d, (4, 5, 7, 8), color); px(d, (7, 6, 13, 7), light); px(d, (12, 8, 13, 10), color)
    elif kind == "toy_car":
        px(d, (3, 8, 13, 11), color); px(d, (5, 6, 10, 7), light); px(d, (4, 12, 5, 13), dark); px(d, (11, 12, 12, 13), dark)
    elif kind == "notebook":
        px(d, (4, 3, 12, 14), color); px(d, (5, 4, 5, 13), light); px(d, (7, 6, 11, 6), (235, 235, 220))
    elif kind == "glasses":
        px(d, (3, 7, 6, 10), color); px(d, (10, 7, 13, 10), color); px(d, (7, 8, 9, 8), color)
    elif kind == "wallet":
        px(d, (3, 5, 13, 12), color); px(d, (4, 6, 12, 7), shade); px(d, (10, 9, 12, 10), light)
    elif kind == "usb_drive":
        px(d, (4, 6, 10, 10), color); px(d, (10, 7, 13, 9), light); px(d, (5, 11, 9, 12), shade)
    else:
        px(d, (5, 3, 11, 13), color); px(d, (7, 5, 9, 7), light); px(d, (6, 13, 10, 14), shade)

    if variant % 3 == 1:
        px(d, (13, 3, 14, 4), (245, 218, 110))
    if variant % 3 == 2:
        px(d, (2, 13, 3, 14), (113, 188, 132))
    return img


def main():
    out = Path("assets/afterblock_textures/items")
    out.mkdir(parents=True, exist_ok=True)
    for i in range(100):
        kind, color = OBJECT_LIBRARY[i % len(OBJECT_LIBRARY)]
        path = out / f"{kind}_{i + 1:03d}.png"
        draw_icon(kind, color, i).save(path)
    for kind, color in OBJECT_LIBRARY:
        draw_icon(kind, color, 0).save(out / f"{kind}_selected.png")
    (out.parent / "README.md").write_text(
        "# AfterBlock texture placeholders\n\n"
        "Generated 64x64 Minecraft-style item textures for museum relic demos. "
        "These are repo-local placeholders for a future resource pack or Paper plugin import.\n",
        encoding="utf-8",
    )
    print(f"generated {len(list(out.glob('*.png')))} textures in {out}")


if __name__ == "__main__":
    main()
