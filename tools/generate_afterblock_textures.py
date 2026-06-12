import json
import math
import shutil
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


TARGET_COUNT = 1200
CUSTOM_MODEL_BASE = 730000


OBJECT_LIBRARY = [
    ("book", (108, 46, 39), "thin_rect"),
    ("earbuds", (232, 235, 232), "paired_dots"),
    ("monitor", (32, 36, 46), "screen"),
    ("school_bag", (85, 99, 138), "bag"),
    ("painting", (176, 63, 48), "framed_square"),
    ("water_bottle", (48, 132, 190), "bottle"),
    ("lamp", (222, 177, 82), "lamp"),
    ("microphone", (42, 42, 48), "cylinder"),
    ("tissue", (226, 226, 216), "box"),
    ("keyboard", (182, 186, 184), "wide_flat"),
    ("charger", (225, 224, 214), "plug"),
    ("mug", (196, 82, 74), "cup"),
    ("shoes", (92, 78, 70), "pair"),
    ("key", (219, 174, 76), "key"),
    ("toy_car", (205, 42, 38), "vehicle"),
    ("notebook", (68, 119, 168), "thin_rect"),
    ("glasses", (38, 38, 42), "glasses"),
    ("wallet", (96, 59, 35), "wide_flat"),
    ("usb_drive", (166, 169, 172), "plug"),
    ("clock", (218, 218, 204), "clock"),
    ("camera", (45, 48, 56), "box_lens"),
    ("pencil", (231, 180, 54), "pencil"),
    ("passport", (46, 72, 126), "thin_rect"),
    ("ring", (224, 190, 88), "ring"),
    ("watch", (52, 60, 66), "watch"),
    ("coin", (226, 176, 63), "coin"),
    ("remote", (50, 52, 58), "remote"),
    ("cassette", (82, 88, 112), "cassette"),
    ("game_controller", (40, 45, 50), "controller"),
    ("photo_frame", (150, 98, 56), "framed_square"),
    ("medicine_box", (212, 216, 205), "box"),
    ("train_ticket", (210, 184, 124), "ticket"),
    ("plush_toy", (180, 130, 92), "plush"),
    ("paint_brush", (159, 83, 45), "brush"),
    ("calculator", (56, 82, 96), "calculator"),
    ("headphones", (45, 48, 58), "headphones"),
    ("polaroid", (235, 226, 204), "photo"),
    ("memory_card", (58, 74, 64), "card"),
    ("lunch_box", (182, 72, 64), "box"),
    ("umbrella", (84, 91, 160), "umbrella"),
]


def shade(color, amount):
    return tuple(max(0, min(255, c + amount)) for c in color)


def px(draw, box, fill, scale=4):
    x1, y1, x2, y2 = box
    draw.rectangle([x1 * scale, y1 * scale, (x2 + 1) * scale - 1, (y2 + 1) * scale - 1], fill=fill)


def draw_icon(kind, color, shape, variant):
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    dark = shade(color, -58)
    mid = color
    light = shade(color, 44)
    ink = (30, 27, 24)
    accent = ((variant * 53) % 180 + 55, (variant * 91) % 180 + 55, (variant * 37) % 180 + 55)

    if shape == "thin_rect":
        px(d, (4, 3, 12, 14), mid); px(d, (4, 3, 5, 14), dark); px(d, (7, 5, 11, 6), light)
    elif shape == "paired_dots":
        px(d, (4, 5, 7, 8), mid); px(d, (10, 5, 13, 8), mid); px(d, (7, 9, 7, 13), light); px(d, (10, 9, 10, 13), light)
    elif shape == "screen":
        px(d, (2, 3, 14, 11), ink); px(d, (3, 4, 13, 10), mid); px(d, (7, 12, 9, 13), dark); px(d, (5, 14, 11, 14), dark)
    elif shape == "bag":
        px(d, (4, 6, 12, 14), mid); px(d, (6, 4, 10, 5), dark); px(d, (5, 8, 11, 9), light); px(d, (4, 10, 5, 13), dark)
    elif shape == "framed_square":
        px(d, (2, 2, 14, 14), dark); px(d, (4, 4, 12, 12), mid); px(d, (7, 5, 10, 8), accent)
    elif shape == "bottle":
        px(d, (6, 2, 10, 4), light); px(d, (5, 5, 11, 14), mid); px(d, (6, 7, 10, 8), (210, 238, 245))
    elif shape == "lamp":
        px(d, (4, 3, 12, 7), light); px(d, (7, 8, 9, 13), dark); px(d, (5, 14, 11, 14), mid)
    elif shape == "cylinder":
        px(d, (6, 3, 10, 10), ink); px(d, (7, 4, 9, 9), mid); px(d, (8, 11, 8, 13), dark); px(d, (5, 14, 11, 14), dark)
    elif shape == "box":
        px(d, (4, 6, 12, 13), mid); px(d, (4, 6, 12, 7), light); px(d, (5, 9, 11, 10), accent)
    elif shape == "wide_flat":
        px(d, (2, 7, 14, 12), mid); px(d, (3, 8, 13, 8), light); px(d, (4, 10, 12, 11), dark)
    elif shape == "plug":
        px(d, (4, 5, 9, 10), mid); px(d, (9, 6, 12, 8), light); px(d, (12, 7, 14, 7), dark)
    elif shape == "cup":
        px(d, (4, 5, 10, 13), mid); px(d, (10, 7, 13, 10), dark); px(d, (5, 4, 9, 4), light)
    elif shape == "pair":
        px(d, (3, 9, 8, 12), mid); px(d, (9, 8, 14, 12), dark); px(d, (4, 12, 14, 13), ink)
    elif shape == "key":
        px(d, (4, 5, 7, 8), mid); px(d, (7, 6, 13, 7), light); px(d, (12, 8, 13, 10), mid)
    elif shape == "vehicle":
        px(d, (3, 8, 13, 11), mid); px(d, (5, 6, 10, 7), light); px(d, (4, 12, 5, 13), ink); px(d, (11, 12, 12, 13), ink)
    elif shape == "glasses":
        px(d, (3, 7, 6, 10), mid); px(d, (10, 7, 13, 10), mid); px(d, (7, 8, 9, 8), mid)
    elif shape == "clock":
        px(d, (5, 4, 11, 10), mid); px(d, (7, 6, 8, 8), ink); px(d, (4, 12, 12, 13), dark)
    elif shape == "box_lens":
        px(d, (3, 6, 13, 12), mid); px(d, (6, 4, 10, 5), light); px(d, (7, 7, 10, 10), ink); px(d, (8, 8, 9, 9), accent)
    elif shape == "pencil":
        px(d, (3, 8, 12, 10), mid); px(d, (13, 8, 14, 10), light); px(d, (2, 8, 2, 10), ink)
    elif shape == "ring":
        px(d, (5, 5, 11, 11), mid); px(d, (7, 7, 9, 9), (0, 0, 0, 0)); px(d, (8, 3, 9, 4), light)
    elif shape == "watch":
        px(d, (7, 2, 9, 5), dark); px(d, (5, 5, 11, 11), mid); px(d, (7, 11, 9, 14), dark); px(d, (7, 7, 9, 9), light)
    elif shape == "coin":
        px(d, (5, 4, 11, 12), mid); px(d, (6, 5, 10, 11), light); px(d, (8, 7, 8, 9), dark)
    elif shape == "remote":
        px(d, (5, 3, 11, 14), mid); px(d, (7, 5, 9, 5), accent); px(d, (7, 8, 9, 11), dark)
    elif shape == "cassette":
        px(d, (3, 5, 13, 12), mid); px(d, (5, 7, 7, 9), ink); px(d, (10, 7, 12, 9), ink); px(d, (5, 10, 11, 10), light)
    elif shape == "controller":
        px(d, (3, 7, 13, 11), mid); px(d, (2, 9, 5, 13), mid); px(d, (11, 9, 14, 13), mid); px(d, (5, 9, 6, 9), light); px(d, (10, 9, 11, 9), accent)
    elif shape == "photo":
        px(d, (4, 3, 12, 14), mid); px(d, (5, 4, 11, 9), accent); px(d, (6, 11, 10, 12), dark)
    elif shape == "card":
        px(d, (4, 5, 12, 12), mid); px(d, (5, 6, 11, 7), light); px(d, (6, 9, 7, 10), ink)
    elif shape == "ticket":
        px(d, (3, 6, 13, 11), mid); px(d, (5, 7, 11, 7), light); px(d, (5, 9, 9, 9), dark)
    elif shape == "plush":
        px(d, (5, 5, 11, 12), mid); px(d, (4, 4, 5, 6), mid); px(d, (11, 4, 12, 6), mid); px(d, (7, 8, 7, 8), ink); px(d, (9, 8, 9, 8), ink)
    elif shape == "brush":
        px(d, (3, 10, 10, 12), dark); px(d, (10, 5, 12, 10), mid); px(d, (12, 3, 13, 5), light)
    elif shape == "calculator":
        px(d, (4, 3, 12, 14), mid); px(d, (5, 4, 11, 6), light)
        for x in (6, 8, 10):
            for y in (8, 10, 12):
                px(d, (x, y, x, y), ink)
    elif shape == "headphones":
        px(d, (4, 4, 12, 6), mid); px(d, (3, 7, 5, 11), mid); px(d, (11, 7, 13, 11), mid)
    elif shape == "umbrella":
        px(d, (3, 5, 13, 8), mid); px(d, (8, 8, 8, 13), dark); px(d, (8, 13, 10, 14), dark)
    else:
        px(d, (5, 3, 11, 13), mid); px(d, (7, 5, 9, 7), light); px(d, (6, 13, 10, 14), dark)

    if variant % 4 == 1:
        px(d, (13, 3, 14, 4), (245, 218, 110))
    elif variant % 4 == 2:
        px(d, (2, 13, 3, 14), (113, 188, 132))
    elif variant % 4 == 3:
        px(d, (13, 13, 14, 14), (185, 120, 215))
    return img


def element_model(kind, texture_ref):
    displays = {
        "gui": {"rotation": [30, 225, 0], "translation": [0, 0, 0], "scale": [0.9, 0.9, 0.9]},
        "ground": {"rotation": [0, 0, 0], "translation": [0, 3, 0], "scale": [0.35, 0.35, 0.35]},
        "fixed": {"rotation": [0, 180, 0], "translation": [0, 0, 0], "scale": [0.7, 0.7, 0.7]},
        "thirdperson_righthand": {"rotation": [75, 45, 0], "translation": [0, 2.5, 0], "scale": [0.38, 0.38, 0.38]},
        "firstperson_righthand": {"rotation": [0, 45, 0], "translation": [0, 2, 0], "scale": [0.4, 0.4, 0.4]},
    }
    shape_elements = {
        "thin_rect": [([4, 2, 6], [12, 14, 8])],
        "paired_dots": [([4, 7, 5], [7, 10, 8]), ([9, 7, 5], [12, 10, 8]), ([7, 3, 6], [8, 8, 7]), ([10, 3, 6], [11, 8, 7])],
        "screen": [([2, 5, 5], [14, 12, 7]), ([7, 3, 6], [9, 5, 8]), ([5, 2, 5], [11, 3, 8])],
        "bag": [([4, 3, 4], [12, 12, 10]), ([6, 12, 5], [10, 14, 9])],
        "framed_square": [([2, 2, 5], [14, 14, 7]), ([4, 4, 4], [12, 12, 8])],
        "bottle": [([5, 2, 5], [11, 12, 10]), ([6, 12, 6], [10, 15, 9])],
        "lamp": [([4, 9, 5], [12, 14, 10]), ([7, 3, 6], [9, 9, 8]), ([5, 2, 5], [11, 3, 10])],
        "cylinder": [([6, 5, 5], [10, 14, 10]), ([7, 2, 6], [9, 5, 9])],
        "box": [([4, 4, 4], [12, 12, 12])],
        "wide_flat": [([2, 5, 5], [14, 10, 8])],
        "plug": [([4, 6, 5], [9, 10, 9]), ([9, 7, 6], [13, 9, 8])],
        "cup": [([4, 4, 4], [10, 12, 10]), ([10, 6, 6], [13, 10, 9])],
        "pair": [([3, 4, 5], [8, 8, 9]), ([8, 6, 5], [14, 10, 9])],
        "key": [([4, 8, 6], [7, 11, 9]), ([7, 9, 7], [14, 10, 8])],
        "vehicle": [([3, 5, 5], [13, 9, 9]), ([5, 9, 6], [10, 11, 8])],
        "glasses": [([3, 7, 6], [6, 10, 8]), ([10, 7, 6], [13, 10, 8]), ([6, 8, 7], [10, 9, 8])],
        "clock": [([5, 4, 5], [11, 12, 9]), ([4, 2, 6], [12, 4, 8])],
        "box_lens": [([3, 5, 5], [13, 11, 9]), ([7, 6, 4], [11, 10, 10])],
        "pencil": [([3, 7, 6], [13, 9, 8]), ([13, 7, 6], [15, 9, 8])],
        "ring": [([5, 5, 5], [11, 11, 7]), ([7, 7, 4], [9, 9, 8])],
        "watch": [([5, 5, 5], [11, 11, 9]), ([7, 2, 6], [9, 5, 8]), ([7, 11, 6], [9, 14, 8])],
        "coin": [([5, 4, 6], [11, 12, 8])],
        "remote": [([5, 2, 5], [11, 14, 8])],
        "cassette": [([3, 5, 5], [13, 12, 8])],
        "controller": [([3, 6, 5], [13, 10, 9]), ([2, 8, 6], [5, 13, 9]), ([11, 8, 6], [14, 13, 9])],
        "photo": [([4, 2, 5], [12, 14, 7])],
        "card": [([4, 5, 5], [12, 12, 7])],
        "ticket": [([3, 6, 5], [13, 11, 7])],
        "plush": [([5, 5, 5], [11, 12, 10]), ([4, 11, 6], [6, 14, 9]), ([10, 11, 6], [12, 14, 9])],
        "brush": [([3, 6, 6], [11, 8, 8]), ([11, 8, 5], [13, 13, 9])],
        "calculator": [([4, 3, 5], [12, 14, 8])],
        "headphones": [([4, 11, 5], [6, 14, 9]), ([10, 11, 5], [12, 14, 9]), ([5, 13, 6], [11, 15, 8])],
        "umbrella": [([3, 9, 5], [13, 13, 9]), ([8, 3, 6], [9, 9, 8])],
    }
    elements = []
    for from_, to_ in shape_elements.get(kind, shape_elements["box"]):
        elements.append(
            {
                "from": from_,
                "to": to_,
                "faces": {
                    face: {"texture": "#all"}
                    for face in ["north", "south", "east", "west", "up", "down"]
                },
            }
        )
    return {
        "credit": "Generated by AfterBlock Museum texture pipeline",
        "textures": {"all": texture_ref, "particle": texture_ref},
        "elements": elements,
        "display": displays,
    }


def render_isometric_preview(kind, color, shape, variant):
    base = draw_icon(kind, color, shape, variant).resize((96, 96), Image.Resampling.NEAREST)
    canvas = Image.new("RGBA", (140, 120), (0, 0, 0, 0))
    shadow = Image.new("RGBA", (92, 36), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.ellipse([8, 8, 84, 28], fill=(0, 0, 0, 70))
    canvas.alpha_composite(shadow, (24, 78))
    canvas.alpha_composite(base.rotate(-18, resample=Image.Resampling.NEAREST, expand=True), (24, 8))
    return canvas


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def build_gallery(manifest, root):
    gallery_dir = root / "gallery"
    gallery_dir.mkdir(parents=True, exist_ok=True)
    thumb_dir = gallery_dir / "previews"
    thumb_dir.mkdir(exist_ok=True)
    preview_count = min(len(manifest), 400)
    for item in manifest[:preview_count]:
        preview = render_isometric_preview(item["kind"], tuple(item["color"]), item["shape"], item["variant"])
        preview.save(thumb_dir / f"{item['id']}.png")

    cards = []
    for item in manifest[:240]:
        cards.append(
            "<article>"
            f"<img src='previews/{item['id']}.png' alt='{item['label']}'>"
            f"<strong>{item['label']}</strong>"
            f"<span>{item['kind']} · CMD {item['custom_model_data']}</span>"
            f"<code>{item['model']}</code>"
            "</article>"
        )
    html = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>AfterBlock Texture Gallery</title>
  <style>
    body {{ margin: 0; background: #11120f; color: #eadfbd; font-family: ui-monospace, Menlo, monospace; }}
    header {{ position: sticky; top: 0; background: #191a16; border-bottom: 2px solid #9d7a42; padding: 18px 24px; z-index: 1; }}
    h1 {{ margin: 0 0 6px; color: #ffd87c; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 14px; padding: 20px; }}
    article {{ background: #201d17; border: 2px solid #5e523d; padding: 10px; min-height: 190px; }}
    img {{ width: 140px; height: 120px; object-fit: contain; display: block; margin: 0 auto 8px; background: #161712; }}
    strong, span, code {{ display: block; overflow-wrap: anywhere; }}
    strong {{ color: #fff0b8; }}
    span {{ color: #bdb08f; margin: 4px 0; }}
    code {{ color: #9fd3b1; font-size: 11px; }}
  </style>
</head>
<body>
  <header>
    <h1>AfterBlock Texture Gallery</h1>
    <div>{len(manifest)} generated item textures and 3D model JSONs. Showing first 240 previews.</div>
  </header>
  <main class="grid">{''.join(cards)}</main>
</body>
</html>
"""
    (gallery_dir / "index.html").write_text(html, encoding="utf-8")

    page_size = 100
    for page, start in enumerate(range(0, min(len(manifest), 400), page_size), 1):
        sheet = Image.new("RGB", (1600, 1200), (20, 21, 18))
        draw = ImageDraw.Draw(sheet)
        draw.text((20, 14), f"AfterBlock generated textures page {page}", fill=(250, 220, 140))
        for offset, item in enumerate(manifest[start : start + page_size]):
            preview_path = thumb_dir / f"{item['id']}.png"
            preview = Image.open(preview_path).convert("RGBA")
            col = offset % 10
            row = offset // 10
            x = 18 + col * 158
            y = 48 + row * 112
            sheet.paste(preview, (x + 8, y), preview)
            draw.text((x, y + 86), item["label"][:18], fill=(235, 224, 190))
            draw.text((x, y + 102), str(item["custom_model_data"]), fill=(159, 210, 176))
        sheet.save(gallery_dir / f"contact_sheet_{page:02d}.png")


def main():
    loose = Path("assets/afterblock_textures/items")
    loose.mkdir(parents=True, exist_ok=True)
    pack = Path("resource-pack/AfterBlockMuseum")
    if pack.exists():
        shutil.rmtree(pack)
    texture_root = pack / "assets/minecraft/textures/item/afterblock"
    model_root = pack / "assets/minecraft/models/item/afterblock"
    texture_root.mkdir(parents=True, exist_ok=True)
    model_root.mkdir(parents=True, exist_ok=True)

    manifest = []
    overrides = []
    for i in range(TARGET_COUNT):
        kind, color, shape = OBJECT_LIBRARY[i % len(OBJECT_LIBRARY)]
        variant = i // len(OBJECT_LIBRARY)
        item_id = f"afterblock_{i + 1:04d}"
        label = f"{kind.replace('_', ' ').title()} {variant + 1:02d}"
        img = draw_icon(kind, color, shape, i)
        loose_name = f"{kind}_{i + 1:04d}.png"
        img.save(loose / loose_name)
        img.save(texture_root / f"{item_id}.png")
        texture_ref = f"minecraft:item/afterblock/{item_id}"
        model = element_model(shape, texture_ref)
        write_json(model_root / f"{item_id}.json", model)
        custom_model_data = CUSTOM_MODEL_BASE + i + 1
        overrides.append({"predicate": {"custom_model_data": custom_model_data}, "model": f"minecraft:item/afterblock/{item_id}"})
        manifest.append(
            {
                "id": item_id,
                "label": label,
                "kind": kind,
                "shape": shape,
                "variant": variant,
                "color": list(color),
                "texture": f"assets/minecraft/textures/item/afterblock/{item_id}.png",
                "model": f"assets/minecraft/models/item/afterblock/{item_id}.json",
                "custom_model_data": custom_model_data,
                "recommended_item": "minecraft:paper",
                "display_strategy": "3D item model with GUI, ground, fixed, first-person, and third-person transforms",
            }
        )

    for kind, color, shape in OBJECT_LIBRARY:
        draw_icon(kind, color, shape, 0).save(loose / f"{kind}_selected.png")

    write_json(
        pack / "pack.mcmeta",
        {
            "pack": {
                "pack_format": 34,
                "description": "AfterBlock Museum generated relic textures and 3D item models",
            }
        },
    )
    write_json(
        pack / "assets/minecraft/models/item/paper.json",
        {"parent": "minecraft:item/generated", "textures": {"layer0": "minecraft:item/paper"}, "overrides": overrides},
    )
    write_json(pack / "afterblock_manifest.json", manifest)
    write_json(Path("assets/afterblock_textures/afterblock_manifest.json"), manifest)
    build_gallery(manifest, Path("assets/afterblock_textures"))

    (Path("assets/afterblock_textures/README.md")).write_text(
        "# AfterBlock generated texture set\n\n"
        f"Generated {len(manifest)} Minecraft-style item textures, 3D item model JSON files, "
        "a resource-pack skeleton, contact sheets, and a browser gallery.\n\n"
        "- Gallery: `assets/afterblock_textures/gallery/index.html`\n"
        "- Resource pack: `resource-pack/AfterBlockMuseum/`\n"
        "- Manifest: `assets/afterblock_textures/afterblock_manifest.json`\n",
        encoding="utf-8",
    )
    print(f"generated {len(manifest)} resource-pack items")


if __name__ == "__main__":
    main()
