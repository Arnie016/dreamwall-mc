import json
import math
import shutil
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


TARGET_COUNT = 3200
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
    ("vinyl_record", (32, 30, 36), "coin"),
    ("desk_plant", (78, 138, 82), "plush"),
    ("sneaker_box", (196, 82, 64), "box"),
    ("metro_card", (234, 188, 70), "card"),
    ("arcade_token", (220, 174, 82), "coin"),
    ("travel_adapter", (218, 218, 206), "plug"),
    ("sketchbook", (218, 205, 174), "thin_rect"),
    ("sunglasses_case", (52, 48, 58), "wide_flat"),
    ("desk_fan", (166, 176, 184), "clock"),
    ("cable_spool", (58, 62, 70), "cassette"),
    ("protein_bar", (154, 92, 54), "wide_flat"),
    ("film_canister", (44, 48, 55), "cylinder"),
    ("mini_tripod", (50, 52, 58), "lamp"),
    ("name_badge", (232, 230, 214), "card"),
    ("sticky_notes", (238, 220, 92), "ticket"),
    ("game_cartridge", (72, 86, 98), "card"),
    ("tea_tin", (72, 130, 118), "box"),
    ("pocket_mirror", (202, 210, 216), "coin"),
    ("luggage_tag", (184, 104, 72), "ticket"),
    ("fountain_pen", (38, 46, 62), "pencil"),
    ("voice_recorder", (55, 62, 70), "remote"),
    ("sd_reader", (68, 72, 78), "plug"),
    ("desk_calendar", (220, 218, 204), "photo"),
    ("mini_speaker", (42, 46, 52), "box_lens"),
    ("wallet_chain", (188, 178, 144), "key"),
    ("paint_tube", (192, 210, 220), "pencil"),
    ("badge_pin", (198, 72, 82), "ring"),
    ("matchbox", (205, 74, 58), "box"),
    ("ram_stick", (46, 112, 82), "wide_flat"),
    ("lucky_charm", (220, 170, 74), "plush"),
]

MATERIALS = [
    ("paper fiber", (232, 220, 190), "matte archival surface"),
    ("brushed metal", (172, 180, 182), "cool edge highlights"),
    ("soft plastic", (204, 210, 214), "rounded satin shell"),
    ("painted wood", (138, 92, 54), "warm visible grain"),
    ("canvas cloth", (190, 174, 142), "woven raised pixels"),
    ("glass glow", (136, 196, 218), "translucent blue glints"),
    ("rubber grip", (54, 58, 62), "dark tactile edges"),
    ("enamel badge", (220, 82, 92), "hard glossy color"),
    ("aged brass", (196, 152, 72), "museum-worn metal"),
    ("screen phosphor", (82, 190, 140), "lit display lines"),
]


def shade(color, amount):
    return tuple(max(0, min(255, c + amount)) for c in color)


def px(draw, box, fill, scale=4):
    x1, y1, x2, y2 = box
    draw.rectangle([x1 * scale, y1 * scale, (x2 + 1) * scale - 1, (y2 + 1) * scale - 1], fill=fill)


def add_variant_marks(draw, variant, accent, ink):
    motif = variant % 8
    if motif == 0:
        return
    if motif in {1, 5}:
        for x in range(4, 13, 3):
            px(draw, (x, 3, x, 13), accent)
    if motif in {2, 6}:
        for y in range(4, 13, 3):
            px(draw, (3, y, 13, y), accent)
    if motif == 3:
        for step in range(4, 13, 2):
            px(draw, (step, step, step, step), accent)
    if motif == 4:
        px(draw, (3, 3, 5, 5), accent)
        px(draw, (11, 11, 13, 13), accent)
    if motif == 5:
        px(draw, (12, 4, 13, 5), ink)
        px(draw, (4, 12, 5, 13), ink)
    if motif == 6:
        px(draw, (7, 3, 9, 3), ink)
        px(draw, (7, 13, 9, 13), ink)
    if motif == 7:
        for x, y in ((4, 5), (8, 7), (12, 10), (6, 12)):
            px(draw, (x, y, x, y), accent)


def blend(a, b, amount):
    return tuple(int(a[i] * (1 - amount) + b[i] * amount) for i in range(3))


def material_for(kind, shape, variant):
    index = (len(kind) * 7 + len(shape) * 11 + variant * 3) % len(MATERIALS)
    name, tint, finish = MATERIALS[index]
    return {"name": name, "tint": tint, "finish": finish}


def apply_material_texture(draw, material, variant):
    tint = material["tint"]
    name = material["name"]
    if "paper" in name or "canvas" in name:
        for y in range(3, 15, 3):
            px(draw, (3, y, 13, y), blend(tint, (70, 60, 45), 0.25))
        for x in range(4, 14, 4):
            px(draw, (x, 3, x, 13), blend(tint, (255, 246, 210), 0.18))
    elif "metal" in name or "brass" in name:
        px(draw, (4, 4, 12, 4), blend(tint, (255, 255, 255), 0.42))
        px(draw, (12, 5, 13, 12), blend(tint, (40, 38, 34), 0.38))
        if variant % 2:
            px(draw, (5, 11, 10, 11), blend(tint, (255, 232, 150), 0.25))
    elif "glass" in name or "screen" in name:
        px(draw, (5, 4, 7, 5), blend(tint, (255, 255, 255), 0.55))
        px(draw, (9, 8, 12, 9), blend(tint, (70, 220, 180), 0.32))
    elif "rubber" in name:
        for x in range(4, 13, 2):
            px(draw, (x, 12, x, 13), blend(tint, (0, 0, 0), 0.35))
    elif "wood" in name:
        for y in (5, 8, 12):
            px(draw, (3, y, 13, y), blend(tint, (84, 45, 22), 0.35))
    elif "enamel" in name:
        px(draw, (5, 5, 10, 5), blend(tint, (255, 255, 255), 0.45))


def draw_icon(kind, color, shape, variant):
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    dark = shade(color, -58)
    mid = color
    light = shade(color, 44)
    ink = (30, 27, 24)
    accent = ((variant * 53) % 180 + 55, (variant * 91) % 180 + 55, (variant * 37) % 180 + 55)
    material = material_for(kind, shape, variant)
    mid = blend(mid, material["tint"], 0.18)
    light = shade(mid, 50)
    dark = shade(mid, -62)

    protected_icon_kinds = {"earbuds", "monitor", "school_bag", "shoes", "clock", "remote"}

    if kind == "earbuds":
        px(d, (5, 7, 6, 13), light)
        px(d, (10, 7, 11, 13), light)
        px(d, (3, 4, 7, 7), mid)
        px(d, (9, 4, 13, 7), mid)
        px(d, (3, 6, 4, 7), ink)
        px(d, (12, 6, 13, 7), ink)
        px(d, (5, 12, 6, 13), (112, 208, 240))
        px(d, (10, 12, 11, 13), (112, 208, 240))
    elif shape == "thin_rect":
        px(d, (4, 3, 12, 14), mid); px(d, (4, 3, 5, 14), dark); px(d, (7, 5, 11, 6), light)
    elif shape == "paired_dots":
        px(d, (4, 5, 7, 8), mid); px(d, (10, 5, 13, 8), mid); px(d, (7, 9, 7, 13), light); px(d, (10, 9, 10, 13), light)
    elif shape == "screen":
        px(d, (2, 3, 14, 11), ink); px(d, (3, 4, 13, 10), mid); px(d, (4, 5, 12, 8), blend(mid, (70, 180, 230), 0.42)); px(d, (7, 11, 9, 13), dark); px(d, (5, 14, 11, 15), dark)
    elif shape == "bag":
        px(d, (4, 5, 12, 14), mid)
        px(d, (5, 4, 11, 5), dark)
        px(d, (6, 3, 10, 4), dark)
        px(d, (5, 7, 11, 9), light)
        px(d, (6, 10, 10, 13), shade(mid, 18))
        px(d, (4, 7, 5, 13), dark)
        px(d, (11, 7, 12, 13), dark)
        px(d, (6, 6, 10, 6), (238, 210, 112))
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
        px(d, (2, 10, 8, 12), mid); px(d, (9, 9, 15, 12), dark)
        px(d, (3, 13, 9, 14), (232, 226, 210)); px(d, (9, 13, 15, 14), (232, 226, 210))
        px(d, (6, 8, 8, 9), light); px(d, (13, 7, 15, 8), light)
        px(d, (4, 10, 6, 10), ink); px(d, (11, 9, 13, 9), ink)
    elif shape == "key":
        px(d, (4, 5, 7, 8), mid); px(d, (7, 6, 13, 7), light); px(d, (12, 8, 13, 10), mid)
    elif shape == "vehicle":
        px(d, (3, 8, 13, 11), mid); px(d, (5, 6, 10, 7), light); px(d, (4, 12, 5, 13), ink); px(d, (11, 12, 12, 13), ink)
    elif shape == "glasses":
        px(d, (3, 7, 6, 10), mid); px(d, (10, 7, 13, 10), mid); px(d, (7, 8, 9, 8), mid)
    elif shape == "clock":
        px(d, (5, 3, 11, 4), dark); px(d, (4, 5, 12, 13), mid); px(d, (5, 6, 11, 12), light); px(d, (8, 7, 8, 10), ink); px(d, (8, 10, 10, 10), ink); px(d, (4, 14, 12, 15), dark)
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
        px(d, (5, 2, 11, 15), mid); px(d, (7, 4, 9, 4), (230, 70, 60))
        for by in (6, 8, 10, 12):
            px(d, (7, by, 7, by), light)
            px(d, (9, by, 9, by), dark)
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
    if kind not in protected_icon_kinds:
        add_variant_marks(d, variant, accent, ink)
        apply_material_texture(d, material, variant)
    return img


def model_variant_profile(shape, variant):
    profiles = [
        {
            "name": "pedestal_front",
            "orientation": "upright pedestal",
            "scale": 1.0,
            "x_shift": 0.0,
            "y_shift": 0.0,
            "z_scale": 1.0,
            "gui_rotation": [30, 225, 0],
            "fixed_rotation": [0, 180, 0],
            "itemdisplay": "ItemDisplay.Transform.FIXED",
        },
        {
            "name": "wall_tilt_left",
            "orientation": "left-tilted wall relic",
            "scale": 0.94,
            "x_shift": -0.35,
            "y_shift": 0.25,
            "z_scale": 0.82,
            "gui_rotation": [30, 210, 0],
            "fixed_rotation": [0, 168, 0],
            "itemdisplay": "ItemDisplay.Transform.HEAD",
        },
        {
            "name": "wall_tilt_right",
            "orientation": "right-tilted wall relic",
            "scale": 0.94,
            "x_shift": 0.35,
            "y_shift": 0.25,
            "z_scale": 0.82,
            "gui_rotation": [30, 240, 0],
            "fixed_rotation": [0, 192, 0],
            "itemdisplay": "ItemDisplay.Transform.HEAD",
        },
        {
            "name": "tabletop_low",
            "orientation": "low tabletop object",
            "scale": 0.86,
            "x_shift": 0.0,
            "y_shift": -0.45,
            "z_scale": 1.25,
            "gui_rotation": [42, 225, 0],
            "fixed_rotation": [8, 180, 0],
            "itemdisplay": "ItemDisplay.Transform.GROUND",
        },
        {
            "name": "tall_showcase",
            "orientation": "tall glass-case object",
            "scale": 1.08,
            "x_shift": 0.0,
            "y_shift": 0.45,
            "z_scale": 0.9,
            "gui_rotation": [25, 220, 0],
            "fixed_rotation": [0, 180, 0],
            "itemdisplay": "ItemDisplay.Transform.FIXED",
        },
        {
            "name": "handheld_diagonal",
            "orientation": "diagonal handheld relic",
            "scale": 0.9,
            "x_shift": 0.0,
            "y_shift": 0.0,
            "z_scale": 0.88,
            "gui_rotation": [35, 235, 12],
            "fixed_rotation": [0, 205, 0],
            "itemdisplay": "ItemDisplay.Transform.THIRDPERSON_RIGHTHAND",
        },
    ]
    bulky_shapes = {"bag", "box", "box_lens", "controller", "plush", "lamp", "bottle"}
    flat_shapes = {"thin_rect", "framed_square", "photo", "ticket", "card", "wide_flat", "screen"}
    profile = dict(profiles[variant % len(profiles)])
    if shape in bulky_shapes and profile["name"].startswith("wall_tilt"):
        profile = dict(profiles[0 if variant % 2 == 0 else 4])
    if shape in flat_shapes and profile["name"] == "tabletop_low":
        profile = dict(profiles[1 + (variant % 2)])
    return profile


def transform_element(from_, to_, profile, variant):
    scale = profile["scale"]
    z_scale = profile["z_scale"]
    x_shift = profile["x_shift"]
    y_shift = profile["y_shift"]
    depth_bias = ((variant % 5) - 2) * 0.08

    def transform_point(point):
        x, y, z = point
        nx = 8 + (x - 8) * scale + x_shift
        ny = 8 + (y - 8) * scale + y_shift
        nz = 8 + (z - 8) * z_scale + depth_bias
        return [
            round(max(0, min(16, nx)), 3),
            round(max(0, min(16, ny)), 3),
            round(max(0, min(16, nz)), 3),
        ]

    a = transform_point(from_)
    b = transform_point(to_)
    return (
        [min(a[0], b[0]), min(a[1], b[1]), min(a[2], b[2])],
        [max(a[0], b[0]), max(a[1], b[1]), max(a[2], b[2])],
    )


def element_model(shape, texture_ref, variant):
    profile = model_variant_profile(shape, variant)
    displays = {
        "gui": {"rotation": profile["gui_rotation"], "translation": [0, 0, 0], "scale": [0.9, 0.9, 0.9]},
        "ground": {"rotation": [0, 0, 0], "translation": [0, 3, 0], "scale": [0.35, 0.35, 0.35]},
        "fixed": {"rotation": profile["fixed_rotation"], "translation": [0, 0, 0], "scale": [0.7, 0.7, 0.7]},
        "thirdperson_righthand": {"rotation": [75, 45, 0], "translation": [0, 2.5, 0], "scale": [0.38, 0.38, 0.38]},
        "firstperson_righthand": {"rotation": [0, 45, 0], "translation": [0, 2, 0], "scale": [0.4, 0.4, 0.4]},
    }
    shape_elements = {
        "thin_rect": [([4, 2, 6], [12, 14, 8])],
        "paired_dots": [([5, 3, 6], [7, 10, 8]), ([9, 3, 6], [11, 10, 8]), ([3, 10, 5], [7, 13, 9]), ([9, 10, 5], [13, 13, 9]), ([4, 11, 4], [5, 12, 6]), ([11, 11, 4], [12, 12, 6])],
        "screen": [([2, 5, 5], [14, 12, 7]), ([3, 6, 4], [13, 11, 5]), ([7, 2, 6], [9, 5, 8]), ([5, 1, 5], [11, 2, 9])],
        "bag": [([4, 3, 4], [12, 12, 10]), ([5, 6, 3], [11, 11, 5]), ([6, 12, 5], [10, 14, 9]), ([3, 5, 5], [4, 12, 9]), ([12, 5, 5], [13, 12, 9]), ([6, 9, 3], [10, 10, 4])],
        "framed_square": [([2, 2, 5], [14, 14, 7]), ([4, 4, 4], [12, 12, 8])],
        "bottle": [([5, 2, 5], [11, 12, 10]), ([6, 12, 6], [10, 15, 9])],
        "lamp": [([4, 9, 5], [12, 14, 10]), ([7, 3, 6], [9, 9, 8]), ([5, 2, 5], [11, 3, 10])],
        "cylinder": [([6, 5, 5], [10, 14, 10]), ([7, 2, 6], [9, 5, 9])],
        "box": [([4, 4, 4], [12, 12, 12])],
        "wide_flat": [([2, 5, 5], [14, 10, 8])],
        "plug": [([4, 6, 5], [9, 10, 9]), ([9, 7, 6], [13, 9, 8])],
        "cup": [([4, 4, 4], [10, 12, 10]), ([10, 6, 6], [13, 10, 9])],
        "pair": [([2, 4, 5], [8, 7, 9]), ([8, 5, 5], [14, 8, 9]), ([2, 3, 5], [8, 4, 10]), ([8, 4, 5], [14, 5, 10])],
        "key": [([4, 8, 6], [7, 11, 9]), ([7, 9, 7], [14, 10, 8])],
        "vehicle": [([3, 5, 5], [13, 9, 9]), ([5, 9, 6], [10, 11, 8])],
        "glasses": [([3, 7, 6], [6, 10, 8]), ([10, 7, 6], [13, 10, 8]), ([6, 8, 7], [10, 9, 8])],
        "clock": [([4, 5, 5], [12, 13, 8]), ([5, 6, 4], [11, 12, 5]), ([7, 3, 6], [9, 5, 8]), ([4, 2, 6], [6, 4, 8]), ([10, 2, 6], [12, 4, 8])],
        "box_lens": [([3, 5, 5], [13, 11, 9]), ([7, 6, 4], [11, 10, 10])],
        "pencil": [([3, 7, 6], [13, 9, 8]), ([13, 7, 6], [15, 9, 8])],
        "ring": [([5, 5, 5], [11, 11, 7]), ([7, 7, 4], [9, 9, 8])],
        "watch": [([5, 5, 5], [11, 11, 9]), ([7, 2, 6], [9, 5, 8]), ([7, 11, 6], [9, 14, 8])],
        "coin": [([5, 4, 6], [11, 12, 8])],
        "remote": [([5, 2, 5], [11, 14, 8]), ([7, 11, 4], [9, 12, 5]), ([7, 8, 4], [8, 9, 5]), ([10, 8, 4], [11, 9, 5]), ([7, 5, 4], [11, 6, 5])],
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
    for index, (from_, to_) in enumerate(shape_elements.get(shape, shape_elements["box"])):
        adjusted_from, adjusted_to = transform_element(from_, to_, profile, variant)
        element = {
            "from": adjusted_from,
            "to": adjusted_to,
            "faces": {
                face: {"texture": "#all"}
                for face in ["north", "south", "east", "west", "up", "down"]
            },
        }
        if profile["name"].startswith("wall_tilt") and index == 0:
            element["rotation"] = {
                "origin": [8, 8, 8],
                "axis": "y",
                "angle": -22.5 if profile["name"].endswith("left") else 22.5,
                "rescale": True,
            }
        elements.append(element)
    return {
        "credit": "Generated by AfterBlock Museum texture pipeline",
        "afterblock_profile": profile,
        "textures": {"all": texture_ref, "particle": texture_ref},
        "elements": elements,
        "display": displays,
    }


def render_isometric_preview(kind, color, shape, variant):
    base = draw_icon(kind, color, shape, variant).resize((96, 96), Image.Resampling.NEAREST)
    canvas = Image.new("RGBA", (164, 136), (0, 0, 0, 0))
    shadow = Image.new("RGBA", (92, 36), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.ellipse([8, 8, 84, 28], fill=(0, 0, 0, 70))
    canvas.alpha_composite(shadow, (36, 90))
    side = Image.new("RGBA", base.size, (0, 0, 0, 0))
    side.alpha_composite(base)
    for offset, alpha in ((10, 70), (6, 92), (3, 110)):
        extrusion = Image.new("RGBA", side.size, (0, 0, 0, 0))
        extrusion.alpha_composite(side)
        r, g, b, a = extrusion.split()
        dark = Image.merge("RGBA", (r.point(lambda p: p * 0.45), g.point(lambda p: p * 0.45), b.point(lambda p: p * 0.45), a.point(lambda p: min(p, alpha))))
        canvas.alpha_composite(dark.rotate(-18, resample=Image.Resampling.NEAREST, expand=True), (32 + offset, 8 + offset))
    canvas.alpha_composite(base.rotate(-18, resample=Image.Resampling.NEAREST, expand=True), (32, 8))
    return canvas


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def build_gallery(manifest, root):
    gallery_dir = root / "gallery"
    gallery_dir.mkdir(parents=True, exist_ok=True)
    thumb_dir = gallery_dir / "previews"
    thumb_dir.mkdir(exist_ok=True)
    for item in manifest:
        preview = render_isometric_preview(item["kind"], tuple(item["color"]), item["shape"], item["variant"])
        preview.save(thumb_dir / f"{item['id']}.png")

    kinds = sorted({item["kind"] for item in manifest})
    shapes = sorted({item["shape"] for item in manifest})
    kind_counts = {kind: sum(1 for item in manifest if item["kind"] == kind) for kind in kinds}
    cards = []
    for item in manifest:
        give_command = (
            f"/give @p minecraft:paper[minecraft:custom_model_data={item['custom_model_data']},"
            f"minecraft:item_name='\"{item['label']}\"'] 1"
        )
        cards.append(
            f"<article data-kind='{item['kind']}' data-shape='{item['shape']}' "
            f"data-profile='{item['model_profile']}' data-material='{item['material']}' "
            f"data-text='{item['label'].lower()} {item['kind']} {item['shape']} {item['model_profile']} {item['orientation']} {item['material']} {item['finish']} {item['custom_model_data']}'>"
            f"<img src='previews/{item['id']}.png' alt='{item['label']}'>"
            f"<strong>{item['label']}</strong>"
            f"<span>{item['kind']} | {item['shape']} | CMD {item['custom_model_data']}</span>"
            f"<span>{item['material']} | {item['finish']}</span>"
            f"<span>{item['model_profile']} | {item['orientation']} | {item['element_count']} cuboids</span>"
            f"<code>{item['model']}</code>"
            f"<button data-command=\"{give_command}\">Copy /give</button>"
            "</article>"
        )
    kind_buttons = ["<button class='filter active' data-kind='all'>all</button>"] + [
        f"<button class='filter' data-kind='{kind}'>{kind} ({kind_counts[kind]})</button>" for kind in kinds
    ]
    html = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>AfterBlock Texture Gallery</title>
  <style>
    body {{ margin: 0; background: #11120f; color: #eadfbd; font-family: ui-monospace, Menlo, monospace; }}
    header {{ position: sticky; top: 0; background: #191a16; border-bottom: 2px solid #9d7a42; padding: 18px 24px; z-index: 1; }}
    h1 {{ margin: 0 0 6px; color: #ffd87c; }}
    .controls {{ display: grid; gap: 10px; margin-top: 14px; }}
    input {{ background: #0f100d; color: #ffe6a3; border: 1px solid #725f37; padding: 10px; font: inherit; }}
    .filters {{ display: flex; flex-wrap: wrap; gap: 8px; max-height: 92px; overflow: auto; }}
    button {{ background: #29251b; color: #ffe6a3; border: 1px solid #7d6436; padding: 7px 9px; font: inherit; cursor: pointer; }}
    button.active, article button:hover {{ background: #6f5425; color: #fff7c8; }}
    .stats {{ color: #bdb08f; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 14px; padding: 20px; }}
    article {{ background: #201d17; border: 2px solid #5e523d; padding: 10px; min-height: 245px; box-shadow: inset 0 0 0 1px #2f281d; }}
    article.hidden {{ display: none; }}
    img {{ width: 164px; height: 136px; object-fit: contain; display: block; margin: 0 auto 8px; background: radial-gradient(circle at 50% 40%, #2d2a20, #161712 68%); }}
    strong, span, code {{ display: block; overflow-wrap: anywhere; }}
    strong {{ color: #fff0b8; }}
    span {{ color: #bdb08f; margin: 4px 0; }}
    code {{ color: #9fd3b1; font-size: 11px; }}
    article button {{ width: 100%; margin-top: 8px; }}
  </style>
</head>
<body>
  <header>
    <h1>AfterBlock Texture Gallery</h1>
    <div>{len(manifest)} generated item textures and 3D model JSONs. Every card has a PNG preview, shape, orientation profile, and CustomModelData command.</div>
    <div class="controls">
      <input id="search" placeholder="Search label, kind, shape, model profile, orientation, or custom model data">
      <div class="filters">{''.join(kind_buttons)}</div>
      <div class="stats"><span id="visible">{len(manifest)}</span> visible / {len(manifest)} total | {len(kinds)} kinds | {len(shapes)} model shapes | {len({item['model_profile'] for item in manifest})} display profiles</div>
    </div>
  </header>
  <main class="grid">{''.join(cards)}</main>
  <script>
    const cards = [...document.querySelectorAll('article')];
    const visible = document.querySelector('#visible');
    const search = document.querySelector('#search');
    let activeKind = 'all';
    function applyFilter() {{
      const q = search.value.trim().toLowerCase();
      let count = 0;
      for (const card of cards) {{
        const kindOk = activeKind === 'all' || card.dataset.kind === activeKind;
        const textOk = !q || card.dataset.text.includes(q);
        const show = kindOk && textOk;
        card.classList.toggle('hidden', !show);
        if (show) count++;
      }}
      visible.textContent = count;
    }}
    document.querySelectorAll('.filter').forEach(button => {{
      button.addEventListener('click', () => {{
        document.querySelectorAll('.filter').forEach(item => item.classList.remove('active'));
        button.classList.add('active');
        activeKind = button.dataset.kind;
        applyFilter();
      }});
    }});
    search.addEventListener('input', applyFilter);
    document.querySelectorAll('article button').forEach(button => {{
      button.addEventListener('click', async () => {{
        await navigator.clipboard.writeText(button.dataset.command);
        button.textContent = 'Copied';
        setTimeout(() => button.textContent = 'Copy /give', 900);
      }});
    }});
  </script>
</body>
</html>
"""
    (gallery_dir / "index.html").write_text(html, encoding="utf-8")
    write_json(
        gallery_dir / "library_report.json",
        {
            "total_items": len(manifest),
            "total_kinds": len(kinds),
            "total_shapes": len(shapes),
            "total_model_profiles": len({item["model_profile"] for item in manifest}),
            "total_materials": len({item["material"] for item in manifest}),
            "kind_counts": kind_counts,
            "shapes": shapes,
            "materials": sorted({item["material"] for item in manifest}),
            "model_profiles": sorted({item["model_profile"] for item in manifest}),
            "custom_model_data_range": [
                min(item["custom_model_data"] for item in manifest),
                max(item["custom_model_data"] for item in manifest),
            ],
            "browser_gallery": "assets/afterblock_textures/gallery/index.html",
            "resource_pack": "resource-pack/AfterBlockMuseum.zip",
        },
    )

    page_size = 100
    for page, start in enumerate(range(0, len(manifest), page_size), 1):
        sheet = Image.new("RGB", (1800, 1400), (20, 21, 18))
        draw = ImageDraw.Draw(sheet)
        draw.text((20, 14), f"AfterBlock generated textures page {page}", fill=(250, 220, 140))
        for offset, item in enumerate(manifest[start : start + page_size]):
            preview_path = thumb_dir / f"{item['id']}.png"
            preview = Image.open(preview_path).convert("RGBA")
            col = offset % 10
            row = offset // 10
            x = 18 + col * 178
            y = 52 + row * 132
            sheet.paste(preview, (x + 8, y), preview)
            draw.text((x, y + 98), item["label"][:18], fill=(235, 224, 190))
            draw.text((x, y + 114), str(item["custom_model_data"]), fill=(159, 210, 176))
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
        material = material_for(kind, shape, variant)
        item_id = f"afterblock_{i + 1:04d}"
        label = f"{kind.replace('_', ' ').title()} {variant + 1:02d}"
        img = draw_icon(kind, color, shape, i)
        loose_name = f"{kind}_{i + 1:04d}.png"
        img.save(loose / loose_name)
        img.save(texture_root / f"{item_id}.png")
        texture_ref = f"minecraft:item/afterblock/{item_id}"
        model = element_model(shape, texture_ref, variant)
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
                "material": material["name"],
                "material_tint": list(material["tint"]),
                "finish": material["finish"],
                "texture": f"assets/minecraft/textures/item/afterblock/{item_id}.png",
                "model": f"assets/minecraft/models/item/afterblock/{item_id}.json",
                "custom_model_data": custom_model_data,
                "recommended_item": "minecraft:paper",
                "model_profile": model["afterblock_profile"]["name"],
                "orientation": model["afterblock_profile"]["orientation"],
                "itemdisplay_transform": model["afterblock_profile"]["itemdisplay"],
                "element_count": len(model["elements"]),
                "display_strategy": "Per-relic 3D item model with materialized PNG surface, cuboid silhouette, variant display pose, GUI, ground, fixed, first-person, and third-person transforms",
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
        "material finishes, variant display profiles, a resource-pack skeleton, contact sheets, and a browser gallery.\n\n"
        "- Gallery: `assets/afterblock_textures/gallery/index.html`\n"
        "- Report: `assets/afterblock_textures/gallery/library_report.json`\n"
        f"- Contact sheets: `assets/afterblock_textures/gallery/contact_sheet_01.png` through `assets/afterblock_textures/gallery/contact_sheet_{math.ceil(len(manifest) / 100):02d}.png`\n"
        "- Resource pack: `resource-pack/AfterBlockMuseum/`\n"
        "- Manifest: `assets/afterblock_textures/afterblock_manifest.json`\n",
        encoding="utf-8",
    )
    print(f"generated {len(manifest)} resource-pack items")


if __name__ == "__main__":
    main()
