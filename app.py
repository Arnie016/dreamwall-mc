import base64
import hashlib
import html
import json
import math
import os
import tempfile
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from io import BytesIO

import gradio as gr
import numpy as np
from PIL import Image, ImageDraw, ImageFont


MODEL_ID = "dreamwall-local-semantic-fingerprint-v1"
GRID = 32
SCALE = 12
PUBLIC_SPACE_URL = "https://build-small-hackathon-dreamwall-mc.hf.space"
RESOURCE_PACK_URL = "https://huggingface.co/spaces/build-small-hackathon/dreamwall-mc/resolve/main/resource-pack/AfterBlockMuseum.zip"
RESOURCE_PACK_SHA1 = "03487f018e2062e254b5ea443396f29d099f8b67"
RESOURCE_PACK_PATH = "resource-pack/AfterBlockMuseum.zip"
PAPER_PLUGIN_JAR_PATH = "server-kit/dreamwall-paper-bridge-0.1.0.jar"
PAPER_PLUGIN_SHA1 = "93c09d2182737b5f7998ebca259e82dbfa2b71c1"
PAPER_PLUGIN_SHA256 = "8046f39b9d53ef2421e6e36b635d7f8b922e3c5759e59adfe044670e1149f0dc"
PREBUILT_WORLD_PATH = "server-kit/afterblock-demo-world.zip"
PREBUILT_WORLD_SHA1 = "d5c5d80daf53f5e72bd8860aea884e221a1b9f84"
PREBUILT_WORLD_SHA256 = "33edcf48d00eca44e8076e5f62f5e3289c6686aecbf24e80349e9a6c2f7ed1f3"
TEXTURE_PAGE_SIZE = 96
DEFAULT_IMPORT_PROMPT = "blue school bag from exam week"
DEFAULT_IMPORT_STORY = "It carried my laptop, exam panic, snacks, and the mornings I kept showing up."
DEFAULT_IMPORT_OWNER = "@Wildstash"


BLOCKS = [
    ("white_wool", (234, 236, 230)),
    ("black_wool", (25, 25, 25)),
    ("gray_wool", (78, 82, 86)),
    ("light_gray_wool", (156, 160, 162)),
    ("brown_wool", (114, 73, 43)),
    ("red_wool", (160, 39, 34)),
    ("orange_wool", (230, 118, 31)),
    ("yellow_wool", (246, 198, 45)),
    ("lime_wool", (96, 187, 50)),
    ("green_wool", (74, 124, 42)),
    ("cyan_wool", (22, 156, 156)),
    ("light_blue_wool", (92, 168, 224)),
    ("blue_wool", (53, 70, 164)),
    ("purple_wool", (126, 61, 181)),
    ("magenta_wool", (190, 67, 181)),
    ("pink_wool", (239, 141, 172)),
    ("sandstone", (218, 203, 143)),
    ("moss_block", (89, 110, 45)),
    ("deepslate", (62, 62, 68)),
    ("amethyst_block", (133, 89, 184)),
    ("prismarine", (99, 156, 151)),
    ("glowstone", (241, 203, 118)),
    ("obsidian", (28, 22, 38)),
    ("sea_lantern", (172, 205, 190)),
]

MOOD_WORDS = {
    "cozy": ["cozy", "warm", "cottage", "soft", "home", "lantern"],
    "cursed": ["cursed", "haunted", "eldritch", "broken", "void", "forbidden"],
    "ancient": ["ancient", "ruin", "temple", "fossil", "myth", "buried"],
    "mechanical": ["machine", "gear", "factory", "robot", "engine", "circuit"],
    "wild": ["forest", "storm", "moss", "ocean", "swamp", "wind"],
    "royal": ["castle", "king", "queen", "gold", "throne", "banner"],
}

CANVAS_SIZE = 12
PLOT_SCALE = 32
GALLERY_ORIGIN_X = -(CANVAS_SIZE // 2) * PLOT_SCALE
GALLERY_ORIGIN_Y = 80
GALLERY_ORIGIN_Z = -(CANVAS_SIZE // 2) * PLOT_SCALE
EXISTING_ARTWORKS = [
    {
        "title": "Bird above the broken sky",
        "player": "anonymous_heron",
        "prompt": "a bird in the sky over a silver tree",
        "x": 4,
        "z": 5,
        "moods": ["wild", "cozy"],
        "value": 72,
    },
    {
        "title": "Company sigil in emerald glass",
        "player": "founder_ghost",
        "prompt": "an ai logo for my company made of emerald glass",
        "x": 5,
        "z": 5,
        "moods": ["mechanical", "royal"],
        "value": 81,
    },
    {
        "title": "Cloud treaty",
        "player": "sky_bidder",
        "prompt": "clouds gathering around a public tree",
        "x": 5,
        "z": 4,
        "moods": ["wild", "ancient"],
        "value": 64,
    },
    {
        "title": "Nether receipt",
        "player": "redacted",
        "prompt": "a cursed vending machine that sells memories",
        "x": 8,
        "z": 8,
        "moods": ["cursed", "mechanical"],
        "value": 69,
    },
]

LIVING_WALL_PROMPTS = [
    "a lonely moon whale carrying broken radio signals",
    "a neon forest growing through an old arcade machine",
    "a thunder bird protecting a tiny public library",
    "glass mushrooms orbiting a redstone lighthouse",
    "a crown made of moss floating over a village gate",
    "a cloud dragon sleeping inside a circuit board",
]

MUSEUM_HALLS = [
    "Hall of Firsts",
    "Hall of Companions",
    "Hall of Turning Points",
    "Hall of Worlds",
    "Hall of Soft Things",
    "Hall of Tools",
    "Hall of Lost Signals",
    "Grand Painting Hall",
    "Animal Spirit Grove",
]

HALL_PROFILES = {
    "Hall of Firsts": {
        "when": "when an object marks a first threshold",
        "world": "sunlit origin cabinets, first-step lamps, gold plaques",
        "minecraft": "warm sandstone, gold pressure plates, first-light redstone lamps",
    },
    "Hall of Companions": {
        "when": "when something stayed close through ordinary days",
        "world": "pocket pedestals, quiet benches, green glass cases",
        "minecraft": "moss blocks, item frames, low lanterns near visitor paths",
    },
    "Hall of Turning Points": {
        "when": "when a choice, exam, trade, or pressure changed direction",
        "world": "angled corridors, copper rails, redstone decision marks",
        "minecraft": "copper blocks, comparator lamps, signs with before/after lines",
    },
    "Hall of Worlds": {
        "when": "when a relic opened a world larger than the room",
        "world": "portal shelves, blue map floors, miniature skylines",
        "minecraft": "blue wool, maps, frames, glowstone portal corners",
    },
    "Hall of Soft Things": {
        "when": "when the memory protects, quiets, or shelters",
        "world": "felt-lit corners, soft rails, low pink glass",
        "minecraft": "pink wool, beds, candles, carpeted alcoves",
    },
    "Hall of Tools": {
        "when": "when the object helped the owner act on the world",
        "world": "workbench rows, grey vaults, calibrated stands",
        "minecraft": "deepslate, anvils, crafting tables, inspection signs",
    },
    "Hall of Lost Signals": {
        "when": "when private signal survives public noise",
        "world": "dim receivers, violet static, archive slits",
        "minecraft": "amethyst, note blocks, redstone repeaters, low particles",
    },
    "Grand Painting Hall": {
        "when": "when imagination becomes a place",
        "world": "large frame walls, myth bays, painted sky panels",
        "minecraft": "item frames, terracotta walls, banner rails, map-art slots",
    },
    "Animal Spirit Grove": {
        "when": "when the artifact behaves like a living companion",
        "world": "moss pens, moonlit tracks, creature-name stones",
        "minecraft": "moss carpets, fences, leaves, particle trails",
    },
}

DEMO_ARTIFACTS = {
    "Star Wars childhood book": {
        "owner_name": "Arnav",
        "owner_handle": "@Wildstash",
        "input_type": "memory_prompt",
        "source_prompt": "a worn Star Wars childhood book with bent corners and a silver spaceship on the cover",
        "memory_text": "I kept reopening it because the galaxy felt bigger than my room.",
    },
    "AirPods from first year of university": {
        "owner_name": "Arnav",
        "owner_handle": "@Wildstash",
        "input_type": "object_photo",
        "source_prompt": "white AirPods from my first year of university",
        "memory_text": "They carried private worlds through public noise during my first year away.",
    },
    "Monitor used for first Bitcoin trade": {
        "owner_name": "Arnav",
        "owner_handle": "@Wildstash",
        "input_type": "object_photo",
        "source_prompt": "a black monitor used for my first Bitcoin trade",
        "memory_text": "A screen where numbers first started feeling like weather.",
    },
    "School bag carried through exams": {
        "owner_name": "Arnav",
        "owner_handle": "@Wildstash",
        "input_type": "object_photo",
        "source_prompt": "a school bag carried through exams",
        "memory_text": "It held pencils, snacks, panic, and the weight of every morning.",
    },
    "Prompted painting: red dragon above childhood home": {
        "owner_name": "Arnav",
        "owner_handle": "@Wildstash",
        "input_type": "painting_prompt",
        "source_prompt": "a red dragon above my childhood home",
        "memory_text": "A fantasy guardian hovering over the place I learned to imagine from.",
    },
}

SOCIAL_HANDLES = [
    "@mossbyte", "@skyreceipt", "@quietbag", "@pixelmira", "@redstoneivy",
    "@lostadapter", "@softsignal", "@bookishnova", "@lampkeeper", "@tinymoon",
    "@schoolghost", "@mintmonitor", "@cloudpocket", "@driftcase", "@noiseferry",
    "@glasssparrow", "@examrunner", "@coppernote", "@homebutton", "@tidyvoid",
]

OBJECT_LIBRARY = [
    ("Star Wars childhood book", "memory_prompt", "a worn Star Wars childhood book with bent corners", "I kept reopening it because the galaxy felt bigger than my room.", "book"),
    ("AirPods", "object_photo", "white AirPods from first year of university", "They carried private worlds through public noise.", "earbuds"),
    ("Bitcoin monitor", "object_photo", "black monitor used for a first Bitcoin trade", "Numbers first started feeling like weather.", "monitor"),
    ("Exam school bag", "object_photo", "school bag carried through exams", "It held pencils, snacks, panic, and every morning.", "school bag"),
    ("Red dragon painting", "painting_prompt", "a red dragon above my childhood home", "A fantasy guardian over the place I learned to imagine.", "painting"),
    ("Water bottle", "object_photo", "scratched blue water bottle", "It waited on every desk like a tiny reservoir.", "water bottle"),
    ("Desk lamp", "object_photo", "warm desk lamp beside late night notes", "It kept one square of the room awake.", "lamp"),
    ("Microphone", "object_photo", "black microphone used for first recordings", "It learned my voice before anyone else did.", "microphone"),
    ("Tissue packet", "object_photo", "small tissue packet from a long train ride", "It was ordinary until the day was not.", "tissue"),
    ("Keyboard", "object_photo", "keyboard with shiny worn keys", "It translated nervous thoughts into work.", "keyboard"),
    ("Phone charger", "object_photo", "fraying white phone charger", "It rescued the last percent of the day.", "charger"),
    ("Coffee mug", "object_photo", "ceramic coffee mug with a chipped handle", "It warmed decisions before they became plans.", "mug"),
    ("Running shoes", "object_photo", "old running shoes with rain marks", "They carried promises the body almost kept.", "shoes"),
    ("House key", "object_photo", "single house key on a faded ring", "It made a door feel like a return.", "key"),
    ("Toy car", "memory_prompt", "tiny red toy car from a childhood shelf", "It was speed before I knew distance.", "toy car"),
    ("Notebook", "object_photo", "notebook full of half-started ideas", "It preserved versions of me that did not ship.", "notebook"),
    ("Glasses", "object_photo", "black glasses with a scratched lens", "They made the world sharper and less certain.", "glasses"),
    ("Wallet", "object_photo", "old wallet with expired cards", "It held small permissions to be outside.", "wallet"),
    ("USB drive", "object_photo", "silver USB drive with unknown files", "It carries a sealed room of forgotten work.", "usb drive"),
    ("Alarm clock", "object_photo", "small alarm clock from exam mornings", "It was the sound of responsibility arriving.", "clock"),
    ("Calculator", "object_photo", "scientific calculator with faded buttons", "It made difficult answers feel briefly mechanical.", "calculator"),
    ("Camera", "object_photo", "compact camera with a scratched lens", "It saved proof that the room once looked different.", "camera"),
    ("Cassette tape", "object_photo", "old cassette tape with a handwritten label", "It held a voice from before everything became searchable.", "cassette"),
    ("Lucky coin", "object_photo", "small lucky coin kept in a wallet", "It was not worth much until it became a ritual.", "coin"),
    ("Game controller", "object_photo", "game controller with worn thumbsticks", "It made imaginary places answer back.", "game controller"),
    ("Headphones", "object_photo", "black headphones used on long nights", "They made a private room around the head.", "headphones"),
    ("Lunch box", "object_photo", "steel lunch box from school days", "It carried home into the middle of the day.", "lunch box"),
    ("Medicine box", "object_photo", "small medicine box in a drawer", "It remembered the days the body needed backup.", "medicine box"),
    ("Memory card", "object_photo", "tiny memory card with old photos", "It kept a city of images in almost no space.", "memory card"),
    ("Paint brush", "object_photo", "paint brush stained with blue acrylic", "It turned hesitation into visible color.", "paint brush"),
    ("Passport", "object_photo", "passport with airport stamps", "It proved the same person could cross many rooms.", "passport"),
    ("Pencil", "object_photo", "short pencil chewed near the eraser", "It carried ideas before they were confident.", "pencil"),
    ("Photo frame", "object_photo", "wooden photo frame beside a bed", "It made one memory stand still on purpose.", "photo frame"),
    ("Plush toy", "object_photo", "soft plush toy from an old shelf", "It was a guardian that never needed batteries.", "plush toy"),
    ("Polaroid", "object_photo", "faded polaroid from a bright afternoon", "It made a square of time feel touchable.", "polaroid"),
    ("Remote", "object_photo", "TV remote with one missing button", "It controlled a room more than it should have.", "remote"),
    ("Ring", "object_photo", "simple ring with a small scratch", "It made a promise small enough to wear.", "ring"),
    ("Train ticket", "object_photo", "creased train ticket from a late ride", "It marked the distance between two versions of the day.", "train ticket"),
    ("Umbrella", "object_photo", "black umbrella with bent ribs", "It made bad weather negotiable.", "umbrella"),
    ("Watch", "object_photo", "old watch that runs a little slow", "It kept time in its own accent.", "watch"),
]


@dataclass
class ArtResult:
    image: Image.Image
    profile: dict
    palette: list
    commands: str
    report: str
    trace: str
    server_packet: str
    canvas_report: str
    valuation_packet: str


def stable_seed(text: str) -> int:
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return int(digest[:16], 16)


def embedding(text: str) -> np.ndarray:
    lowered = text.lower()
    vec = np.zeros(96, dtype=np.float32)
    words = [word.strip(".,!?;:()[]{}\"'") for word in lowered.split()]
    for idx, word in enumerate(words):
        if not word:
            continue
        digest = hashlib.blake2b(word.encode("utf-8"), digest_size=32).digest()
        for offset, byte in enumerate(digest):
            slot = (byte + idx * 17 + offset * 7) % len(vec)
            vec[slot] += ((byte / 255.0) * 2.0 - 1.0) * (1.0 + min(len(word), 12) / 12.0)
    for mood, mood_words in MOOD_WORDS.items():
        hits = sum(1 for word in mood_words if word in lowered)
        if hits:
            mood_seed = stable_seed(mood)
            rng = np.random.default_rng(mood_seed)
            vec += rng.normal(0, 0.22 * hits, size=len(vec)).astype(np.float32)
    if not np.any(vec):
        vec[0] = 1.0
    norm = float(np.linalg.norm(vec))
    return vec / max(norm, 1e-6)


def top_moods(text: str, vec: np.ndarray) -> list[str]:
    lowered = text.lower()
    scored = []
    for mood, words in MOOD_WORDS.items():
        lexical = sum(1 for word in words if word in lowered) * 0.28
        mood_vec = embedding(" ".join(words))
        semantic = float(np.dot(vec, mood_vec))
        scored.append((semantic + lexical, mood))
    return [mood for _, mood in sorted(scored, reverse=True)[:3]]


def palette_from_vector(vec: np.ndarray, seed: int, moods: list[str]) -> list[tuple[str, tuple[int, int, int]]]:
    rng = np.random.default_rng(seed)
    block_vecs = np.array([rgb for _, rgb in BLOCKS], dtype=np.float32) / 255.0
    anchors = np.abs(vec[: len(BLOCKS)]) + 1e-4
    weights = anchors / max(float(anchors.sum()), 1e-6)
    chosen = list(rng.choice(len(BLOCKS), size=7, replace=False, p=weights))

    mood_boosts = {
        "cozy": ["orange_wool", "yellow_wool", "glowstone", "brown_wool"],
        "cursed": ["obsidian", "purple_wool", "black_wool", "amethyst_block"],
        "ancient": ["sandstone", "moss_block", "deepslate", "brown_wool"],
        "mechanical": ["gray_wool", "light_gray_wool", "deepslate", "cyan_wool"],
        "wild": ["moss_block", "green_wool", "prismarine", "sea_lantern"],
        "royal": ["yellow_wool", "red_wool", "purple_wool", "blue_wool"],
    }
    for mood in moods:
        for name in mood_boosts.get(mood, []):
            idx = next(i for i, block in enumerate(BLOCKS) if block[0] == name)
            if idx not in chosen:
                chosen[-1] = idx
                break
    return [BLOCKS[i] for i in chosen]


def generate_grid(vec: np.ndarray, seed: int, palette: list) -> np.ndarray:
    rng = np.random.default_rng(seed)
    grid = np.zeros((GRID, GRID), dtype=np.int32)
    freq_a = 1.4 + abs(vec[3]) * 5
    freq_b = 1.2 + abs(vec[9]) * 4
    symmetry = abs(vec[12]) > 0.19
    center_bias = abs(vec[27])

    for y in range(GRID):
        for x in range(GRID):
            nx = (x / GRID) - 0.5
            ny = (y / GRID) - 0.5
            wave = math.sin((nx * freq_a + vec[1]) * math.pi * 2)
            wave += math.cos((ny * freq_b + vec[2]) * math.pi * 2)
            ring = math.sin((math.hypot(nx, ny) * (6 + abs(vec[18]) * 12) + vec[4]) * math.pi)
            noise = rng.normal(0, 0.42)
            score = wave + ring * (0.7 + center_bias) + noise
            idx = int(abs(score * 997 + vec[(x + y) % len(vec)] * 113)) % len(palette)
            grid[y, x] = idx
    if symmetry:
        grid[:, GRID // 2 :] = np.fliplr(grid[:, : GRID // 2])
    return grid


def render_grid(grid: np.ndarray, palette: list) -> Image.Image:
    img = Image.new("RGB", (GRID * SCALE, GRID * SCALE), (0, 0, 0))
    draw = ImageDraw.Draw(img)
    for y in range(GRID):
        for x in range(GRID):
            _, color = palette[int(grid[y, x])]
            draw.rectangle(
                [x * SCALE, y * SCALE, (x + 1) * SCALE - 1, (y + 1) * SCALE - 1],
                fill=color,
            )
    for i in range(0, GRID * SCALE, SCALE * 4):
        draw.line([(i, 0), (i, GRID * SCALE)], fill=(35, 28, 22), width=1)
        draw.line([(0, i), (GRID * SCALE, i)], fill=(35, 28, 22), width=1)
    return img


def compact_commands(grid: np.ndarray, palette: list, origin: str) -> str:
    commands = [
        "# Paste these into Minecraft with WorldEdit installed.",
        "# Stand near the gallery wall. Set pos1/pos2 manually if needed.",
        f"# Suggested origin: {origin}",
        "//wand",
        "//pos1",
        "//pos2",
        "# Build the 32x32 mural as wool/block stripes. Each line is one row.",
    ]
    for y in range(GRID):
        runs = []
        start = 0
        current = int(grid[y, 0])
        for x in range(1, GRID + 1):
            if x == GRID or int(grid[y, x]) != current:
                block = palette[current][0]
                runs.append(f"{start}-{x - 1}:{block}")
                if x < GRID:
                    start = x
                    current = int(grid[y, x])
        commands.append(f"# row {y:02d}: " + ", ".join(runs))
    commands.append("# Plugin hook idea: convert the row runs into setblock/fill calls at the wall anchor.")
    return "\n".join(commands)


def row_runs(grid: np.ndarray, palette: list) -> list[list[dict]]:
    rows = []
    for y in range(GRID):
        runs = []
        start = 0
        current = int(grid[y, 0])
        for x in range(1, GRID + 1):
            if x == GRID or int(grid[y, x]) != current:
                runs.append(
                    {
                        "x1": start,
                        "x2": x - 1,
                        "y": y,
                        "block": palette[current][0],
                    }
                )
                if x < GRID:
                    start = x
                    current = int(grid[y, x])
        rows.append(runs)
    return rows


def prompt_density(prompt: str) -> float:
    words = [word.strip(".,!?;:()[]{}\"'").lower() for word in prompt.split()]
    words = [word for word in words if word]
    if not words:
        return 0.0
    unique_ratio = len(set(words)) / len(words)
    long_word_ratio = sum(1 for word in words if len(word) >= 7) / len(words)
    symbol_hits = sum(1 for word in words if word in {"bird", "tree", "cloud", "logo", "castle", "machine", "temple", "sky"})
    return min(1.0, unique_ratio * 0.55 + long_word_ratio * 0.25 + min(symbol_hits, 4) * 0.05)


def plot_for_seed(seed: int) -> dict:
    x = seed % CANVAS_SIZE
    z = (seed // CANVAS_SIZE) % CANVAS_SIZE
    return {
        "x": int(x),
        "z": int(z),
        "world_x": int((x - CANVAS_SIZE // 2) * PLOT_SCALE),
        "world_z": int((z - CANVAS_SIZE // 2) * PLOT_SCALE),
        "size": PLOT_SCALE,
    }


def nearby_artworks(plot: dict) -> list[dict]:
    near = []
    for art in EXISTING_ARTWORKS:
        distance = abs(art["x"] - plot["x"]) + abs(art["z"] - plot["z"])
        if distance <= 2:
            near.append({**art, "distance": distance})
    return sorted(near, key=lambda item: (item["distance"], -item["value"]))[:3]


def fusion_lines(prompt: str, player: str, moods: list[str], plot: dict) -> list[str]:
    neighbors = nearby_artworks(plot)
    if not neighbors:
        return [
            "No nearby fusion yet. This plot becomes a new anchor others can build around.",
            "Value grows if future prompts land nearby and reuse its symbols.",
        ]

    lines = []
    for art in neighbors:
        shared_moods = sorted(set(moods).intersection(art["moods"]))
        if shared_moods:
            reason = f"shared {', '.join(shared_moods)} mood"
        else:
            reason = "spatial collision without mood overlap"
        lines.append(
            f"{player} fuses with {art['player']} at ({art['x']}, {art['z']}): "
            f"{reason}. New concept: {prompt} woven into '{art['title']}'."
        )
    return lines


def valuation(prompt: str, moods: list[str], palette_names: list[str], plot: dict) -> dict:
    density = prompt_density(prompt)
    neighbors = nearby_artworks(plot)
    adjacency = min(1.0, sum(max(0, 3 - item["distance"]) for item in neighbors) / 6)
    mood_diversity = len(set(moods)) / max(1, len(MOOD_WORDS))
    palette_rarity = len(set(palette_names).intersection({"obsidian", "amethyst_block", "sea_lantern", "glowstone"})) / 4
    score = 25 + density * 28 + adjacency * 24 + mood_diversity * 12 + palette_rarity * 16
    votes = int(3 + score // 8 + len(neighbors) * 2)
    reserve = int(max(5, score * 1.7))
    return {
        "creative_value": round(score, 2),
        "syntactic_density": round(density, 3),
        "context_adjacency": round(adjacency, 3),
        "mood_diversity": round(mood_diversity, 3),
        "palette_rarity": round(palette_rarity, 3),
        "suggested_votes": votes,
        "demo_reserve_points": reserve,
        "market_note": "Demo points only; no real-money sale or blockchain required for the hackathon.",
    }


def canvas_report(prompt: str, player: str, moods: list[str], palette_names: list[str], plot: dict) -> tuple[str, str]:
    value = valuation(prompt, moods, palette_names, plot)
    fusions = fusion_lines(prompt, player, moods, plot)
    report = [
        f"Plot assigned: ({plot['x']}, {plot['z']}) -> Minecraft origin ({plot['world_x']}, 80, {plot['world_z']})",
        f"Creative value: {value['creative_value']} demo points",
        f"Suggested opening auction reserve: {value['demo_reserve_points']} demo points",
        "",
        "Why this plot has value:",
        f"- syntactic density: {value['syntactic_density']}",
        f"- context adjacency: {value['context_adjacency']}",
        f"- mood diversity: {value['mood_diversity']}",
        f"- palette rarity: {value['palette_rarity']}",
        "",
        "Fusion events:",
    ]
    report.extend(f"- {line}" for line in fusions)
    packet = {
        "protocol": "dreamwall.market.v1",
        "plot": plot,
        "valuation": value,
        "fusion_events": fusions,
        "auction": {
            "mode": "demo_points",
            "reserve": value["demo_reserve_points"],
            "votes": value["suggested_votes"],
            "real_money": False,
            "blockchain": False,
        },
    }
    return "\n".join(report), json.dumps(packet, indent=2)


def object_guess_for(input_type: str, source_prompt: str, memory_text: str) -> str:
    text = f"{source_prompt} {memory_text}".lower()
    guesses = [
        ("phone", ["phone", "iphone", "android", "smartphone", "mobile"]),
        ("water bottle", ["water bottle", "waater", "bottle", "canteen", "thermos"]),
        ("plush toy", ["teddy", "teddy bear", "bear", "plush", "soft toy", "stuffed"]),
        ("sticker", ["sticker", "decal", "label", "logo", "openai"]),
        ("shoes", ["shoe", "shoes", "sneaker", "sneakers", "trainers"]),
        ("book", ["book", "novel", "comic", "star wars", "cover"]),
        ("earbuds", ["airpods", "earpods", "earbuds", "headphones", "music"]),
        ("monitor", ["monitor", "screen", "display", "trade", "bitcoin"]),
        ("school bag", ["bag", "backpack", "exams", "school"]),
        ("painting", ["painting", "dragon", "prompted", "canvas"]),
        ("animal spirit", ["pet", "animal", "dog", "cat", "bird", "creature"]),
        ("tool", ["tool", "keyboard", "mouse", "camera", "phone"]),
    ]
    for guess, hints in guesses:
        if any(hint in text for hint in hints):
            return guess
    if input_type == "painting_prompt":
        return "prompted painting"
    if input_type == "animal_spirit":
        return "animal spirit"
    return "personal relic"


def hall_for_artifact(input_type: str, object_guess: str, source_prompt: str, memory_text: str, seed: int) -> tuple[str, str]:
    text = f"{object_guess} {source_prompt} {memory_text}".lower()
    if input_type == "painting_prompt":
        return "Grand Painting Hall", "paintings that were imagined before they were found"
    if input_type == "animal_spirit" or any(word in text for word in ["pet", "animal", "dog", "cat", "bird", "creature"]):
        return "Animal Spirit Grove", "the artifact behaves more like a companion than an object"
    if any(word in text for word in ["first", "university", "bitcoin", "started"]):
        return "Hall of Firsts", "the memory marks a first threshold"
    if any(word in text for word in ["teddy", "plush", "soft toy", "sleep", "guardian"]):
        return "Hall of Soft Things", "the memory is quiet, protective, and intimate"
    if any(word in text for word in ["sticker", "decal", "logo", "signal", "lost", "radio", "noise"]):
        return "Hall of Lost Signals", "the artifact carries private signal through public static"
    if any(word in text for word in ["airpods", "bag", "bottle", "water", "phone", "shoe", "friend", "carried", "companion"]):
        return "Hall of Companions", "it stayed close to the owner through ordinary days"
    if any(word in text for word in ["exam", "trade", "turning", "changed", "panic"]):
        return "Hall of Turning Points", "the object sits near a decision or pressure point"
    if any(word in text for word in ["star wars", "galaxy", "home", "world", "dragon"]):
        return "Hall of Worlds", "it opened a world larger than the room around it"
    if any(word in text for word in ["soft", "noise", "private", "morning"]):
        return "Hall of Soft Things", "the memory is quiet, protective, and intimate"
    if any(word in text for word in ["monitor", "tool", "screen", "keyboard", "camera"]):
        return "Hall of Tools", "the artifact helped the owner act on the world"
    hall = MUSEUM_HALLS[seed % len(MUSEUM_HALLS)]
    return hall, "the museum placed it by symbolic resonance"


def museum_zone_for(hall: str, seed: int) -> str:
    zones = {
        "Hall of Firsts": ["threshold alcove", "first-light row", "origin cabinet"],
        "Hall of Companions": ["pocket gallery", "everyday pedestal", "quiet bench"],
        "Hall of Turning Points": ["pressure corridor", "exam arch", "decision stair"],
        "Hall of Worlds": ["portal bay", "map room", "myth shelf"],
        "Hall of Soft Things": ["hush wing", "warm glass case", "felt-lit corner"],
        "Hall of Tools": ["workbench row", "instrument vault", "copper desk"],
        "Hall of Lost Signals": ["static aisle", "radio archive", "dim receiver"],
        "Grand Painting Hall": ["large frame wall", "dragon bay", "painted sky"],
        "Animal Spirit Grove": ["moss enclosure", "companion path", "moonlit pen"],
    }
    choices = zones.get(hall, ["west wing"])
    return choices[seed % len(choices)]


def curation_scores(
    source_prompt: str,
    memory_text: str,
    input_type: str,
    moods: list[str],
    palette_names: list[str],
    plot: dict,
) -> dict:
    text = f"{source_prompt} {memory_text}".lower()
    density = prompt_density(text)
    neighbors = nearby_artworks(plot)
    adjacency = min(1.0, sum(max(0, 3 - item["distance"]) for item in neighbors) / 6)
    palette_rarity = len(set(palette_names).intersection({"obsidian", "amethyst_block", "sea_lantern", "glowstone"})) / 4
    def score(words: list[str], base: float = 28.0) -> int:
        hits = sum(1 for word in words if word in text)
        return int(min(100, base + density * 35 + hits * 14))

    scores = {
        "nostalgia": score(["childhood", "school", "first", "home", "kept", "morning"]),
        "symbolism": score(["dragon", "galaxy", "signal", "cover", "weather", "guardian"]),
        "identity": score(["my", "first", "owner", "university", "trade"], 34),
        "companionship": score(["carried", "airpods", "bag", "private", "through"], 30),
        "transformation": score(["first", "trade", "exam", "changed", "started"], 26),
        "rarity": int(min(100, 35 + len(set(moods)) * 10 + density * 25)),
        "palette_rarity": int(round(palette_rarity * 100)),
        "adjacency_resonance": int(round(adjacency * 100)),
        "visitor_echoes": int(min(100, 12 + len(neighbors) * 17 + density * 34)),
    }
    weighted = (
        scores["nostalgia"] * 0.16
        + scores["symbolism"] * 0.14
        + scores["identity"] * 0.14
        + scores["companionship"] * 0.12
        + scores["transformation"] * 0.12
        + scores["rarity"] * 0.1
        + scores["palette_rarity"] * 0.08
        + scores["adjacency_resonance"] * 0.08
        + scores["visitor_echoes"] * 0.06
    )
    scores["curation_score"] = int(round(weighted))
    return scores


def spirit_for_artifact(title: str, object_guess: str, memory_text: str, hall: str, seed: int) -> dict:
    traits_bank = {
        "book": ["wide-eyed", "paper-worn", "portal-minded"],
        "earbuds": ["private", "signal-carrying", "soft-spoken"],
        "monitor": ["watchful", "electric", "threshold-bound"],
        "school bag": ["patient", "burdened", "loyal"],
        "phone": ["signal-lit", "pocket-sized", "watchful"],
        "water bottle": ["clear", "steady", "everyday"],
        "plush toy": ["soft", "protective", "sleep-worn"],
        "sticker": ["signal-marked", "thin", "identity-bound"],
        "shoes": ["road-worn", "patient", "routine-bound"],
        "painting": ["mythic", "paint-lit", "protective"],
        "animal spirit": ["restless", "companionable", "wild"],
        "personal relic": ["quiet", "symbolic", "half-remembered"],
    }
    traits = traits_bank.get(object_guess, traits_bank["personal relic"])
    suffix = ["mote", "keeper", "echo", "sprite", "shade", "wisp"][seed % 6]
    spirit_name = "".join(word.capitalize() for word in keywords_for_title(title)[:1]) + suffix.capitalize()
    first_line = f"I am what remained when {object_guess} became a place."
    if "airpods" in object_guess or object_guess == "earbuds":
        first_line = "I carried private worlds through public noise."
    elif object_guess == "book":
        first_line = "I opened a galaxy small enough to fit in your hands."
    elif object_guess == "monitor":
        first_line = "I watched numbers become weather."
    elif object_guess == "school bag":
        first_line = "I carried the mornings you were not ready for."
    elif object_guess == "phone":
        first_line = "I kept private signals close enough to answer."
    elif object_guess == "water bottle":
        first_line = "I kept ordinary stamina within reach."
    elif object_guess == "plush toy":
        first_line = "I guarded sleep without needing to explain why."
    elif object_guess == "sticker":
        first_line = "I turned a surface into a signal."
    elif object_guess == "shoes":
        first_line = "I carried the route until it became routine."
    elif object_guess == "painting":
        first_line = "I guard the home that imagination returned to."
    questions = [
        "What do you remember?",
        "Why are you in this hall?",
        "What should visitors notice?",
    ]
    responses = [
        first_line,
        f"The curator placed me in {hall} because this memory still has a shape.",
        f"Look for the detail that does not shout: {memory_text[:110]}",
    ]
    return {
        "spirit_name": spirit_name,
        "spirit_traits": traits,
        "spirit_first_line": first_line,
        "rules": [
            "speak only from the object, memory, and artifact lore",
            "do not behave like a generic assistant",
            "answer as a quiet museum presence",
        ],
        "sample_visitor_questions": questions,
        "sample_spirit_responses": responses,
    }


def resonance_links_for_artifact(hall: str, moods: list[str], plot: dict) -> list[dict]:
    links = []
    for art in nearby_artworks(plot):
        shared = sorted(set(moods).intersection(art["moods"]))
        links.append(
            {
                "title": art["title"],
                "creator": art["player"],
                "distance": art["distance"],
                "resonance": "shared mood" if shared else "nearby museum placement",
                "shared_moods": shared,
                "hall_echo": hall,
            }
        )
    return links


def passport_html(artifact: dict) -> str:
    palette = artifact["palette"][:5]
    swatches = "".join(
        f"<span class='museum-swatch' title='{name}' style='background: rgb({rgb[0]}, {rgb[1]}, {rgb[2]})'></span>"
        for name, rgb in [next((block for block in BLOCKS if block[0] == item), ("stone", (120, 120, 120))) for item in palette]
    )
    coords = artifact["minecraft_coordinates"]
    item = artifact.get("resource_pack_item", {})
    share_url = artifact.get("share_url") or artifact_share_url(artifact)
    share_fragment = artifact_passport_fragment(artifact)
    qr_payload = artifact.get("qr_payload") or share_url
    qr_src = qr_code_data_uri(qr_payload)
    qr = (
        f"<img class='passport-qr-image' src='{qr_src}' alt='QR code for this relic'>"
        if qr_src
        else qr_matrix_html(qr_payload)
    )
    preview_url = artifact_preview_url(artifact)
    preview = (
        f"<img class='passport-artifact-image' src='{html_escape(preview_url)}' alt='{html_escape(artifact['object_guess'])} picture'>"
        if preview_url
        else f"<div class='passport-object-mark'>{swatches}</div>"
    )
    return f"""
    <section class="passport-card" id="afterblock-passport-{html_escape(artifact['artifact_id'])}">
      <header class="passport-header">
        <div>
          <div class="passport-kicker">AfterBlock Passport</div>
          <h2>{html_escape(artifact['title'])}</h2>
          <p class="passport-owner">{html_escape(owner_display(artifact))} · {html_escape(artifact['object_guess'])}</p>
        </div>
        <div class="passport-share">
          <div class="passport-share-actions">
            <a class="passport-share-link" href="{html_escape(share_fragment)}">Open scan</a>
            <a class="passport-share-icon" href="{html_escape(share_url)}" target="_blank" rel="noreferrer" aria-label="Open share link" title="Open share link"><span aria-hidden="true">&#8599;</span></a>
          </div>
          <span class="hf-icon">HF</span>
          <span>scan passport</span>
        </div>
      </header>
      <div class="passport-grid">
        <div class="passport-preview">
          {preview}
          <strong>{html_escape(artifact['object_guess'].title())}</strong>
          <em>{html_escape(compact_text(artifact['memory_text'], 96))}</em>
        </div>
        <div class="passport-facts">
          <div class="coordinate-cards">
            <span><small>X</small><strong>{coords['x']}</strong></span>
            <span><small>Y</small><strong>{coords['y']}</strong></span>
            <span><small>Z</small><strong>{coords['z']}</strong></span>
            <span><small>Item code</small><strong>{item.get('custom_model_data', 0)}</strong></span>
          </div>
          <div class="passport-route">
            <strong>{html_escape(artifact['hall'])}</strong>
            <span>{html_escape(artifact['zone'])}</span>
            <span>Plot {artifact['plot']['x']}, {artifact['plot']['z']}</span>
          </div>
          <p><strong>Caption</strong> {html_escape(artifact['memory_text'])}</p>
          <p><strong>Plaque</strong> {html_escape(artifact['plaque_line'])}</p>
          <div class="passport-scan">
            {qr}
            <div>
              <strong>Scan result</strong>
              <p>Opens a scanned passport panel with this relic's route, exact XYZ, and Minecraft command.</p>
              <span>{html_escape(share_url)}</span>
            </div>
          </div>
        </div>
      </div>
    </section>
    """


def relic_profile_html(artifact: dict) -> str:
    item = artifact.get("resource_pack_item", {})
    coords = artifact["minecraft_coordinates"]
    share_url = artifact.get("share_url") or artifact_share_url(artifact)
    share_fragment = artifact_passport_fragment(artifact)
    command = minecraft_give_command(artifact)
    return f"""
    <section class="relic-profile-page" id="relic-profile-{html_escape(artifact['artifact_id'])}">
      <header>
        <div>
          <span class="profile-kicker">{html_escape(artifact['hall'])} / {html_escape(artifact['zone'])}</span>
          <h2>{html_escape(artifact['title'])}</h2>
          <p>{html_escape(owner_display(artifact))} · CMD {item.get('custom_model_data', 0)} · XYZ {coords['x']} {coords['y']} {coords['z']}</p>
        </div>
        <div class="profile-share-actions">
          <a href="{html_escape(share_fragment)}" class="profile-share">Open scan</a>
          <a href="{html_escape(share_url)}" target="_blank" rel="noreferrer" class="profile-share-icon" aria-label="Open share link" title="Open share link"><span aria-hidden="true">&#8599;</span></a>
        </div>
      </header>
      <div class="profile-grid">
        <article>
          <h3>History</h3>
          <p>{html_escape(artifact.get('memory_text', artifact.get('plaque_line', '')))}</p>
          <p class="profile-lore">{html_escape(artifact.get('spirit_first_line', artifact.get('plaque_line', '')))}</p>
        </article>
        <article>
          <h3>Minecraft Relic</h3>
          <code>{html_escape(command)}</code>
          <p>{html_escape(artifact.get('lore_short', artifact.get('placement_reason', '')))}</p>
        </article>
      </div>
    </section>
    """


def floor_map_html(artifact: dict) -> str:
    cells = []
    for z in range(CANVAS_SIZE):
        for x in range(CANVAS_SIZE):
            active = x == artifact["plot"]["x"] and z == artifact["plot"]["z"]
            near = abs(x - artifact["plot"]["x"]) + abs(z - artifact["plot"]["z"]) <= 2
            label = "X" if active else ""
            cells.append(
                f"<span class='floor-cell {'active' if active else ''} {'near' if near and not active else ''}' "
                f"title='Plot {x}, {z}'>{label}</span>"
            )
    return f"""
    <section class="passport-map-card">
      <header>
        <h3>Museum floor grid</h3>
        <p>Hover the grid to preview selection. The active plot pulses at {artifact['plot']['x']}, {artifact['plot']['z']}.</p>
      </header>
      <div class='floor-map'>{''.join(cells)}</div>
    </section>
    """


def html_escape(value) -> str:
    return html.escape(str(value or ""), quote=True)


def owner_display(artifact: dict) -> str:
    handle = (artifact.get("owner_handle") or "").strip()
    if handle:
        return handle
    return (artifact.get("owner_name") or "anonymous visitor").strip()


def minecraft_give_command(artifact: dict) -> str:
    item = artifact.get("resource_pack_item", {})
    custom_model_data = item.get("custom_model_data", 0)
    return f"/give @p minecraft:paper[minecraft:custom_model_data={custom_model_data}] 1"


def artifact_share_url(artifact: dict) -> str:
    return f"{PUBLIC_SPACE_URL}/{artifact_passport_fragment(artifact)}"


def artifact_passport_fragment(artifact: dict) -> str:
    token = artifact_share_token(artifact)
    return f"#passport={token}"


def artifact_share_token(artifact: dict) -> str:
    item = artifact.get("resource_pack_item", {})
    coords = artifact.get("minecraft_coordinates", {})
    payload = {
        "type": "afterblock.passport.v1",
        "artifact_id": artifact.get("artifact_id", "unknown"),
        "title": compact_text(artifact.get("title", "AfterBlock Relic"), 72),
        "owner": compact_text(owner_display(artifact), 32),
        "object": compact_text(artifact.get("object_guess", "relic"), 32),
        "hall": compact_text(artifact.get("hall", "AfterBlock Museum"), 42),
        "zone": compact_text(artifact.get("zone", "Museum route"), 38),
        "caption": compact_text(artifact.get("memory_text", artifact.get("plaque_line", "")), 180),
        "command": minecraft_give_command(artifact),
        "xyz": {
            "x": coords.get("x", ""),
            "y": coords.get("y", ""),
            "z": coords.get("z", ""),
        },
        "cmd": item.get("custom_model_data", 0),
    }
    encoded = base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode("utf-8")).decode("ascii")
    return encoded.rstrip("=")


def artifact_preview_url(artifact: dict) -> str:
    item = artifact.get("resource_pack_item", {})
    item_id = item.get("id", "missing")
    if item_id and item_id != "missing":
        return texture_preview_url(item_id)
    return ""


def qr_code_data_uri(payload: str) -> str:
    try:
        import qrcode
    except Exception:
        return ""

    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=7,
        border=3,
    )
    qr.add_data(payload)
    qr.make(fit=True)
    image = qr.make_image(fill_color="#12100c", back_color="#f8edcf").convert("RGB")
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def qr_matrix_html(payload: str) -> str:
    seed = stable_seed(payload)
    cells = []
    for y in range(11):
        for x in range(11):
            finder = (
                (x < 3 and y < 3)
                or (x > 7 and y < 3)
                or (x < 3 and y > 7)
            )
            on = finder or ((seed >> ((x * 11 + y) % 61)) & 1)
            cells.append(f"<span class='{'on' if on else ''}'></span>")
    return f"<div class='mini-qr' aria-label='Share QR code'>{''.join(cells)}</div>"


def coordinates_html(artifact: dict) -> str:
    coords = artifact["minecraft_coordinates"]
    plot = artifact["plot"]
    item = artifact.get("resource_pack_item", {})
    return f"""
    <section class="waypoint-strip">
      <div>
        <span>X</span>
        <strong>{coords['x']}</strong>
      </div>
      <div>
        <span>Y</span>
        <strong>{coords['y']}</strong>
      </div>
      <div>
        <span>Z</span>
        <strong>{coords['z']}</strong>
      </div>
      <div>
        <span>Plot</span>
        <strong>{plot['x']}, {plot['z']}</strong>
      </div>
      <div>
        <span>CMD</span>
        <strong>{item.get('custom_model_data', 0)}</strong>
      </div>
    </section>
    """


def hall_for_plot_cell(plot_x: int, plot_z: int) -> str:
    region_x = min(2, max(0, plot_x // 4))
    region_z = min(2, max(0, plot_z // 4))
    return MUSEUM_HALLS[region_z * 3 + region_x]


def living_route_map_html(artifact: dict) -> str:
    coords = artifact["minecraft_coordinates"]
    plot = artifact["plot"]
    plot_x = int(plot["x"])
    plot_z = int(plot["z"])
    entry_col = CANVAS_SIZE // 2
    entry_x = GALLERY_ORIGIN_X + ((CANVAS_SIZE - 1) * PLOT_SCALE) // 2
    entry_z = GALLERY_ORIGIN_Z - 18
    elbow_x = coords["x"]
    elbow_z = entry_z
    cells = []
    route_min = min(entry_col, plot_x)
    route_max = max(entry_col, plot_x)
    for z in range(CANVAS_SIZE):
        for x in range(CANVAS_SIZE):
            hall = hall_for_plot_cell(x, z)
            cell_classes = ["map-cell"]
            if z == 0 and route_min <= x <= route_max:
                cell_classes.append("route")
            if x == plot_x and 0 <= z <= plot_z:
                cell_classes.append("route")
            if x == entry_col and z == 0:
                cell_classes.append("entry")
            if x == plot_x and z == plot_z:
                cell_classes.append("target")
            hall_rgb = hall_color(hall)
            hall_hex = hex_color(hall_rgb)
            label = f"{x},{z}"
            title = "YOU ARE HERE" if "entry" in cell_classes else label
            if "target" in cell_classes:
                title = f"{artifact['title']} plot {label}"
            cells.append(
                f"<span class='{' '.join(cell_classes)}' style='--hall-color:{hall_hex}' title='{html_escape(title)}'>"
                f"<b>{html_escape(label)}</b></span>"
            )
    return f"""
    <section class="living-route-map">
      <div class="route-map-copy">
        <span>Live route</span>
        <h4>YOU ARE HERE to {html_escape(artifact['title'])}</h4>
        <p>The Space preview uses the same 12x12 grid, origin, plot size, and L-shaped route that the Paper bridge builds in Minecraft.</p>
      </div>
      <div class="route-map-grid" aria-label="12 by 12 AfterBlock Minecraft plot map">
        {''.join(cells)}
      </div>
      <div class="route-map-proof">
        <div><span>Entry beacon</span><strong>X {entry_x} Y {GALLERY_ORIGIN_Y} Z {entry_z}</strong></div>
        <div><span>Route elbow</span><strong>X {elbow_x} Y {GALLERY_ORIGIN_Y} Z {elbow_z}</strong></div>
        <div><span>Relic pad</span><strong>X {coords['x']} Y {coords['y']} Z {coords['z']}</strong></div>
        <div><span>Formula</span><strong>{GALLERY_ORIGIN_X} + plot * {PLOT_SCALE}</strong></div>
      </div>
      <div class="route-map-legend">
        <span><b class="legend-entry"></b> YOU ARE HERE</span>
        <span><b class="legend-route"></b> lit route</span>
        <span><b class="legend-target"></b> relic plot</span>
      </div>
    </section>
    """


def minecraft_campus_view_html(artifact: dict) -> str:
    coords = artifact["minecraft_coordinates"]
    plot = artifact["plot"]
    plot_x = int(plot["x"])
    plot_z = int(plot["z"])
    entry_col = CANVAS_SIZE // 2
    entry_x = GALLERY_ORIGIN_X + ((CANVAS_SIZE - 1) * PLOT_SCALE) // 2
    entry_z = GALLERY_ORIGIN_Z - 18
    tile_w = 30
    tile_h = 16
    origin_left = 250
    origin_top = 28

    def iso_position(x: float, z: float) -> tuple[float, float]:
        return (
            origin_left + (x - z) * (tile_w / 2),
            origin_top + (x + z) * (tile_h / 2),
        )

    route_min = min(entry_col, plot_x)
    route_max = max(entry_col, plot_x)
    tiles = []
    for z in range(CANVAS_SIZE):
        for x in range(CANVAS_SIZE):
            hall = hall_for_plot_cell(x, z)
            classes = ["campus-tile"]
            if z == 0 and route_min <= x <= route_max:
                classes.append("route")
            if x == plot_x and 0 <= z <= plot_z:
                classes.append("route")
            if x == plot_x and z == plot_z:
                classes.append("target")
            if x == entry_col and z == 0:
                classes.append("entry-proxy")
            left, top = iso_position(x, z)
            label = f"{x},{z}"
            title = f"{hall} plot {label}"
            if x == plot_x and z == plot_z:
                title = f"{artifact['title']} at plot {label}"
            tiles.append(
                f"<span class='{' '.join(classes)}' style='left:{left:.1f}px;top:{top:.1f}px;--hall-color:{hex_color(hall_color(hall))}' title='{html_escape(title)}'>"
                f"<b>{html_escape(label)}</b></span>"
            )

    gates = []
    for index, hall in enumerate(MUSEUM_HALLS):
        region_x = index % 3
        region_z = index // 3
        gate_x = region_x * 4 + 1.5
        gate_z = region_z * 4 + 1.5
        left, top = iso_position(gate_x, gate_z)
        gates.append(
            f"<span class='campus-gate' style='left:{left:.1f}px;top:{top - 20:.1f}px;--hall-color:{hex_color(hall_color(hall))}' title='{html_escape(hall)}'>"
            f"<b>{html_escape(hall.replace('Hall of ', '').replace('Grand ', ''))}</b></span>"
        )

    entry_left, entry_top = iso_position(entry_col, -1.2)
    target_left, target_top = iso_position(plot_x, plot_z)
    return f"""
    <section class="minecraft-campus-view">
      <div class="campus-heading">
        <span>In-world view</span>
        <h4>Entry beacon to relic plot</h4>
        <p>The diamonds, hall gates, route lights, and target pad use the same plot grid and XYZ formula as the Paper museum builder.</p>
      </div>
      <div class="campus-stage" aria-label="Isometric Minecraft-style AfterBlock campus">
        <div class="campus-stage-inner">
          {''.join(tiles)}
          {''.join(gates)}
          <span class="campus-entry-beacon" style="left:{entry_left:.1f}px;top:{entry_top:.1f}px" title="YOU ARE HERE at X {entry_x} Y {GALLERY_ORIGIN_Y} Z {entry_z}"><b>YOU<br>ARE<br>HERE</b></span>
          <span class="campus-relic-pin" style="left:{target_left:.1f}px;top:{target_top - 42:.1f}px" title="{html_escape(artifact['title'])}"><b>{html_escape(compact_text(artifact['title'], 18))}</b></span>
        </div>
      </div>
      <div class="campus-proof-strip">
        <span>Entry X {entry_x} Y {GALLERY_ORIGIN_Y} Z {entry_z}</span>
        <span>Plot {plot_x},{plot_z}</span>
        <span>Relic X {coords['x']} Y {coords['y']} Z {coords['z']}</span>
      </div>
    </section>
    """


def waypointcraft_html(artifact: dict) -> str:
    coords = artifact["minecraft_coordinates"]
    item = artifact.get("resource_pack_item", {})
    command = minecraft_give_command(artifact)
    living_map = living_route_map_html(artifact)
    campus_view = minecraft_campus_view_html(artifact)
    return f"""
    <section class="waypoint-card">
      <header>
        <h3>Placement Route</h3>
        <p>{html_escape(artifact['hall'])} / {html_escape(artifact['zone'])}</p>
      </header>
      <div class="waypoint-grid">
        <div><span>World XYZ</span><strong>{coords['x']} {coords['y']} {coords['z']}</strong></div>
        <div><span>CustomModelData</span><strong>{item.get('custom_model_data', 0)}</strong></div>
        <div><span>Base item</span><strong>{html_escape(item.get('recommended_item', 'minecraft:paper'))}</strong></div>
        <div><span>Model</span><strong>{html_escape(item.get('model', 'afterblock:item/missing'))}</strong></div>
      </div>
      {campus_view}
      {living_map}
      <code>{html_escape(command)}</code>
    </section>
    """


def server_setup_html() -> str:
    return f"""
    <section class="server-setup">
      <div>
        <h2>Minecraft Server Setup</h2>
        <p>The Space is the creation terminal. The Paper server is the persistent museum: one 12x12 campus, 144 exact plot addresses, and every relic packet lands at its generated XYZ.</p>
      </div>
      <div class="server-grid">
        <article>
          <span>1</span>
          <h3>Upload</h3>
          <p>Download the Paper server kit below, then upload the included plugin jar and resource pack.</p>
          <p><code>plugins/dreamwall-paper-bridge-0.1.0.jar</code></p>
          <p><code>AfterBlockMuseum.zip</code></p>
        </article>
        <article>
          <span>2</span>
          <h3>Load Pack</h3>
          <p><code>/dreamwall pack</code></p>
          <p>Pack URL: <code>{html_escape(RESOURCE_PACK_URL)}</code></p>
        </article>
        <article>
          <span>3</span>
          <h3>Build Museum</h3>
          <p><code>/dreamwall museum build</code></p>
          <p>Creates the living 12x12 entry atlas, hall gates, memory spine, and entry beacon at plot (0,0) XYZ <code>-192 80 -192</code>. Verify it with <code>/dreamwall museum check</code>.</p>
        </article>
        <article>
          <span>4</span>
          <h3>Place Relics</h3>
          <p><code>/dreamwall import</code></p>
          <p>Imports a Space packet at the generated coordinate, lights the route, sets the compass target, and gives the route compass. Use <code>/dreamwall import here</code> for fast nearby proof.</p>
        </article>
      </div>
      <div class="server-formula">
        <strong>Coordinate contract</strong>
        <code>world_x = {GALLERY_ORIGIN_X} + plot_x * {PLOT_SCALE}</code>
        <code>world_z = {GALLERY_ORIGIN_Z} + plot_z * {PLOT_SCALE}</code>
        <code>world_y = {GALLERY_ORIGIN_Y}</code>
      </div>
      <p class="server-note">For the hackathon demo: use the included prebuilt world as a fast base, then run the museum builder once to refresh the entry atlas. Import the configured relic so the item appears at the exact map address, marks the entry atlas, and gets a route compass, engraved nameplate, lectern passport, and right-click profile button.</p>
    </section>
    """


def server_handoff_html(artifact: dict) -> str:
    coords = artifact["minecraft_coordinates"]
    item = artifact.get("resource_pack_item", {})
    cmd = item.get("custom_model_data", 0)
    return f"""
    <section class="relic-server-handoff">
      <div>
        <span>Live Paper handoff</span>
        <strong>{html_escape(artifact['title'])}</strong>
        <p>/dreamwall import places this exact relic at plot {artifact['plot']['x']}, {artifact['plot']['z']} with an engraved nameplate, lectern passport, route compass, and profile button.</p>
      </div>
      <div class="handoff-proof">
        <b>XYZ {coords['x']} {coords['y']} {coords['z']}</b>
        <b>CMD {cmd}</b>
      </div>
    </section>
    """


def demo_path_html() -> str:
    return f"""
    <section class="demo-path">
      <header>
        <h2>Best Hackathon Demo Path</h2>
        <p>Keep the story simple: the Space is the museum terminal, Minecraft is the persistent place where the memory lives.</p>
      </header>
      <div class="demo-path-grid">
        <article>
          <span>What works</span>
          <ul>
            <li>One ordinary object becomes a hall, profile, passport, item model, and exact Minecraft coordinate.</li>
            <li>The same `CustomModelData` appears in the 3D preview, passport, packet, resource pack, and Paper bridge.</li>
            <li>The server proof is physical: a visitor gets a route compass and walks from `YOU ARE HERE` to the generated plot.</li>
          </ul>
        </article>
        <article>
          <span>What to avoid</span>
          <ul>
            <li>Do not lead with generic AI generation, blockchain, auctions, or a huge feature list.</li>
            <li>Do not spend the video browsing texture shelves unless a judge asks.</li>
            <li>Do not describe the spirit as a chatbot; it is the relic profile and museum lore.</li>
          </ul>
        </article>
      </div>
      <div class="judge-scorecard">
        <article>
          <span>Winning signal</span>
          <strong>One memory becomes a place</strong>
          <p>Lead with the Space creating a relic, then prove that the same relic exists at an exact Minecraft coordinate.</p>
        </article>
        <article>
          <span>Risk to cut</span>
          <strong>Do not demo a feature buffet</strong>
          <p>Skip auctions, large texture browsing, and abstract spirit talk unless a judge asks. They dilute the Minecraft proof.</p>
        </article>
        <article>
          <span>Judge proof</span>
          <strong>Walk the route</strong>
          <p>Show <code>/dreamwall museum check</code>, the route compass, the engraved nameplate, the lectern passport, and the profile button.</p>
        </article>
        <article>
          <span>Why this is hard to copy</span>
          <strong>Space-to-server contract</strong>
          <p>The packet, resource pack, server kit, exact XYZ formula, and visible install card all describe the same museum state.</p>
        </article>
      </div>
      <ol class="demo-script">
        <li><b>0:00</b> Type one relic and story caption in Place in Museum.</li>
        <li><b>0:25</b> Show the generated Minecraft-style model, hall, plot, and command.</li>
        <li><b>0:50</b> Open Passport, scan/share link, and show the exact XYZ.</li>
        <li><b>1:15</b> Open Packet briefly so judges see `dreamwall.museum.v1`.</li>
        <li><b>1:35</b> Switch to Minecraft and run the proof commands; call out the verified living entry atlas.</li>
        <li><b>2:05</b> Show the atlas target, then hold the route compass and follow the lit floor from `YOU ARE HERE` to the relic.</li>
        <li><b>2:30</b> Show the resource-pack item, read the engraved nameplate, open the lectern passport, then right-click the profile button for the relic history.</li>
      </ol>
      <div class="demo-command-strip">
        <code>/dreamwall pack</code>
        <code>/dreamwall museum build</code>
        <code>/dreamwall museum check</code>
        <code>/dreamwall import</code>
      </div>
      <p class="demo-closing-line">Closing line: AfterBlock turns the things people would throw away into places they can visit.</p>
      <div class="demo-proof-note">
        <span>Coordinate proof</span>
        <code>world_x = {GALLERY_ORIGIN_X} + plot_x * {PLOT_SCALE}</code>
        <code>world_y = {GALLERY_ORIGIN_Y}</code>
        <code>world_z = {GALLERY_ORIGIN_Z} + plot_z * {PLOT_SCALE}</code>
      </div>
    </section>
    """


def clean_text(value: str, fallback: str) -> str:
    cleaned = " ".join(str(value or "").split())
    return cleaned or fallback


def yaml_value(value: str) -> str:
    return json.dumps(" ".join(str(value or "").split()))


def server_kit_text(artifact: dict) -> str:
    coords = artifact["minecraft_coordinates"]
    item = artifact.get("resource_pack_item", {})
    command = minecraft_give_command(artifact)
    config = f"""space-url: "{PUBLIC_SPACE_URL}"
resource-pack-url: "{RESOURCE_PACK_URL}"
resource-pack-sha1: "{RESOURCE_PACK_SHA1}"
offer-resource-pack-on-join: false
poll-enabled: false
poll-seconds: 30
default-import-prompt: {yaml_value(artifact.get("source_prompt", DEFAULT_IMPORT_PROMPT))}
default-import-story: {yaml_value(artifact.get("memory_text", DEFAULT_IMPORT_STORY))}
default-import-owner: {yaml_value(artifact.get("owner_handle") or artifact.get("owner_name") or DEFAULT_IMPORT_OWNER)}
gallery-world: "world"
canvas-size: {CANVAS_SIZE}
plot-size: {PLOT_SCALE}
gallery-origin:
  x: {GALLERY_ORIGIN_X}
  y: {GALLERY_ORIGIN_Y}
  z: {GALLERY_ORIGIN_Z}
gallery-facing: "east"
"""
    total_plots = CANVAS_SIZE * CANVAS_SIZE
    return "\n".join(
        [
            "AFTERBLOCK MINECRAFT SERVER KIT",
            "",
            f"Relic: {artifact['title']}",
            f"Owner: {owner_display(artifact)}",
            f"Route: {artifact['hall']} / {artifact['zone']}",
            f"Plot: {artifact['plot']['x']}, {artifact['plot']['z']}",
            f"XYZ: {coords['x']} {coords['y']} {coords['z']}",
            f"CustomModelData: {item.get('custom_model_data', 0)}",
            f"Give command: {command}",
            "",
            "1) Upload these files to PebbleHost",
            "plugins/dreamwall-paper-bridge-0.1.0.jar",
            "AfterBlockMuseum.zip",
            "",
            "2) plugins/DreamWall/config.yml",
            config.rstrip(),
            "",
            "3) First-run in-game commands",
            "/dreamwall pack",
            "/dreamwall museum build",
            "/dreamwall museum check",
            "/dreamwall import",
            "",
            "4) Expected proof",
            "AfterBlock museum check:",
            f"Plot pads: {total_plots}/{total_plots}",
            f"Relic focus blocks: {total_plots}/{total_plots}",
            "YOU ARE HERE beacon: present",
            f"Imported relic lands at XYZ {coords['x']} {coords['y']} {coords['z']} with CMD {item.get('custom_model_data', 0)}, a route compass, an engraved nameplate, a readable passport lectern, and a right-click profile button.",
            "",
            "5) Live Space endpoint used by the Paper bridge",
            f"{PUBLIC_SPACE_URL}/gradio_api/call/quick_curate",
            "",
            "6) Bundle checksums",
            f"dreamwall-paper-bridge-0.1.0.jar sha1={PAPER_PLUGIN_SHA1}",
            f"AfterBlockMuseum.zip sha1={RESOURCE_PACK_SHA1}",
        ]
    )


def server_config_kit_text(
    space_url: str = PUBLIC_SPACE_URL,
    resource_pack_url: str = RESOURCE_PACK_URL,
    resource_pack_sha1: str = RESOURCE_PACK_SHA1,
    gallery_world: str = "world",
    offer_pack_on_join: bool = False,
    import_prompt: str = DEFAULT_IMPORT_PROMPT,
    import_story: str = DEFAULT_IMPORT_STORY,
    import_owner: str = DEFAULT_IMPORT_OWNER,
) -> str:
    config, clean_space_url, _, _, _ = server_config_yaml(
        space_url,
        resource_pack_url,
        resource_pack_sha1,
        gallery_world,
        offer_pack_on_join,
        import_prompt,
        import_story,
        import_owner,
    )
    return "\n".join(
        [
            "AFTERBLOCK PAPER SERVER CONFIG",
            "",
            "Paste this into plugins/DreamWall/config.yml after uploading dreamwall-paper-bridge-0.1.0.jar.",
            "",
            config.rstrip(),
            "",
            "First-run commands",
            "/dreamwall pack",
            "/dreamwall museum build",
            "/dreamwall museum check",
            "/dreamwall import",
            "",
            "Default relic imported by /dreamwall import",
            f"Prompt: {clean_text(import_prompt, DEFAULT_IMPORT_PROMPT)}",
            f"Story: {clean_text(import_story, DEFAULT_IMPORT_STORY)}",
            f"Owner: {clean_text(import_owner, DEFAULT_IMPORT_OWNER)}",
            "",
            "Coordinate contract kept fixed for judge proof",
            f"world_x = {GALLERY_ORIGIN_X} + plot_x * {PLOT_SCALE}",
            f"world_y = {GALLERY_ORIGIN_Y}",
            f"world_z = {GALLERY_ORIGIN_Z} + plot_z * {PLOT_SCALE}",
            "",
            "Live endpoint used by /dreamwall import",
            f"{clean_space_url}/gradio_api/call/quick_curate",
            "",
            "Included downloads",
            "Paper plugin: server-kit/dreamwall-paper-bridge-0.1.0.jar",
            "Resource pack: resource-pack/AfterBlockMuseum.zip",
            "Prebuilt world: server-kit/afterblock-demo-world.zip",
            "ZIP metadata: afterblock-server-profile.json and afterblock-demo-proof.json",
            "Upload helper: UPLOAD_TO_SERVER.md and install-afterblock-paper.sh",
        ]
    )


def server_config_yaml(
    space_url: str = PUBLIC_SPACE_URL,
    resource_pack_url: str = RESOURCE_PACK_URL,
    resource_pack_sha1: str = RESOURCE_PACK_SHA1,
    gallery_world: str = "world",
    offer_pack_on_join: bool = False,
    import_prompt: str = DEFAULT_IMPORT_PROMPT,
    import_story: str = DEFAULT_IMPORT_STORY,
    import_owner: str = DEFAULT_IMPORT_OWNER,
) -> tuple[str, str, str, str, str]:
    clean_space_url = (space_url or PUBLIC_SPACE_URL).strip().rstrip("/")
    clean_pack_url = (resource_pack_url or RESOURCE_PACK_URL).strip()
    clean_pack_sha1 = (resource_pack_sha1 or RESOURCE_PACK_SHA1).strip()
    clean_gallery_world = " ".join(str(gallery_world or "world").split()) or "world"
    clean_import_prompt = clean_text(import_prompt, DEFAULT_IMPORT_PROMPT)
    clean_import_story = clean_text(import_story, DEFAULT_IMPORT_STORY)
    clean_import_owner = clean_text(import_owner, DEFAULT_IMPORT_OWNER)
    offer_pack = "true" if bool(offer_pack_on_join) else "false"
    config = f"""space-url: "{clean_space_url}"
resource-pack-url: "{clean_pack_url}"
resource-pack-sha1: "{clean_pack_sha1}"
offer-resource-pack-on-join: {offer_pack}
poll-enabled: false
poll-seconds: 30
default-import-prompt: {yaml_value(clean_import_prompt)}
default-import-story: {yaml_value(clean_import_story)}
default-import-owner: {yaml_value(clean_import_owner)}
gallery-world: "{clean_gallery_world}"
canvas-size: {CANVAS_SIZE}
plot-size: {PLOT_SCALE}
gallery-origin:
  x: {GALLERY_ORIGIN_X}
  y: {GALLERY_ORIGIN_Y}
  z: {GALLERY_ORIGIN_Z}
gallery-facing: "east"
"""
    return config, clean_space_url, clean_pack_url, clean_pack_sha1, clean_gallery_world


def server_demo_proof_manifest(
    clean_space_url: str,
    clean_pack_url: str,
    clean_pack_sha1: str,
    clean_gallery_world: str,
    clean_import_prompt: str,
    clean_import_story: str,
    clean_import_owner: str,
) -> dict:
    return {
        "type": "afterblock.paper-demo-proof.v1",
        "space_url": clean_space_url,
        "live_endpoint": f"{clean_space_url}/gradio_api/call/quick_curate",
        "default_import": {
            "prompt": clean_import_prompt,
            "story": clean_import_story,
            "owner": clean_import_owner,
        },
        "coordinate_contract": {
            "world": clean_gallery_world,
            "canvas_size": CANVAS_SIZE,
            "plot_scale": PLOT_SCALE,
            "total_plots": CANVAS_SIZE * CANVAS_SIZE,
            "origin": {
                "x": GALLERY_ORIGIN_X,
                "y": GALLERY_ORIGIN_Y,
                "z": GALLERY_ORIGIN_Z,
            },
            "formula": "world_x = -192 + plot_x * 32; world_y = 80; world_z = -192 + plot_z * 32",
        },
        "resource_pack": {
            "url": clean_pack_url,
            "sha1": clean_pack_sha1,
            "textures": 3200,
            "models": 3200,
            "paper_overrides": 3200,
        },
        "bundle": {
            "plugin_sha1": PAPER_PLUGIN_SHA1,
            "plugin_sha256": PAPER_PLUGIN_SHA256,
            "prebuilt_world_sha1": PREBUILT_WORLD_SHA1,
            "prebuilt_world_sha256": PREBUILT_WORLD_SHA256,
        },
        "expected_commands": [
            "/dreamwall pack",
            "/dreamwall museum build",
            "/dreamwall museum check",
            "/dreamwall import",
        ],
        "expected_proof": [
            "museum check reports 144/144 plot pads",
            "YOU ARE HERE beacon is present",
            "living entry atlas is present",
            "route compass points from entry to the generated plot",
            "entry atlas marks the imported relic plot",
            "relic appears with an engraved nameplate, lectern passport, and profile button",
        ],
        "blocked_external_step": "PebbleHost upload requires the panel/SFTP password outside this ZIP.",
    }


def server_owner_profile_manifest(
    clean_space_url: str,
    clean_pack_url: str,
    clean_pack_sha1: str,
    clean_gallery_world: str,
    clean_import_prompt: str,
    clean_import_story: str,
    clean_import_owner: str,
) -> dict:
    return {
        "type": "afterblock.server-profile.v1",
        "purpose": "Share this profile with a Paper server owner so they can install the same persistent AfterBlock museum configured in the Space.",
        "space": {
            "url": clean_space_url,
            "quick_curate_endpoint": f"{clean_space_url}/gradio_api/call/quick_curate",
        },
        "server": {
            "minecraft_world": clean_gallery_world,
            "resource_pack_url": clean_pack_url,
            "resource_pack_sha1": clean_pack_sha1,
            "requires_secret": "Only the server panel or SFTP secret is external. No secret is stored in this kit.",
        },
        "default_import": {
            "prompt": clean_import_prompt,
            "story": clean_import_story,
            "owner": clean_import_owner,
        },
        "upload_map": [
            {
                "kit_path": "plugins/dreamwall-paper-bridge-0.1.0.jar",
                "server_path": "plugins/dreamwall-paper-bridge-0.1.0.jar",
                "reason": "Paper command bridge for /dreamwall pack, museum build, museum check, and import.",
            },
            {
                "kit_path": "plugins/DreamWall/config.yml",
                "server_path": "plugins/DreamWall/config.yml",
                "reason": "Connects the server to this Space, resource pack, fixed coordinate contract, and default relic.",
            },
            {
                "kit_path": "AfterBlockMuseum.zip",
                "server_path": "AfterBlockMuseum.zip",
                "reason": "Minecraft resource pack with 3200 item textures/models and paper overrides.",
            },
            {
                "kit_path": "afterblock-demo-world.zip",
                "server_path": "afterblock-demo-world.zip",
                "reason": "Optional prebuilt memory-spine world for a fast hackathon base. Run /dreamwall museum build once after install to refresh the latest entry atlas.",
            },
        ],
        "first_run_commands": [
            "/dreamwall pack",
            "/dreamwall museum build",
            "/dreamwall museum check",
            "/dreamwall import",
        ],
        "verification_commands": [
            "/dreamwall museum check",
            "/dreamwall import here",
        ],
        "helper_files": [
            "UPLOAD_TO_SERVER.md",
            "install-afterblock-paper.sh",
        ],
        "coordinate_contract": {
            "world": clean_gallery_world,
            "origin": {"x": GALLERY_ORIGIN_X, "y": GALLERY_ORIGIN_Y, "z": GALLERY_ORIGIN_Z},
            "plot_scale": PLOT_SCALE,
            "canvas_size": CANVAS_SIZE,
            "formula": "world_x = -192 + plot_x * 32; world_y = 80; world_z = -192 + plot_z * 32",
        },
    }


def server_owner_install_card_html(
    space_url: str = PUBLIC_SPACE_URL,
    resource_pack_url: str = RESOURCE_PACK_URL,
    resource_pack_sha1: str = RESOURCE_PACK_SHA1,
    gallery_world: str = "world",
    offer_pack_on_join: bool = False,
    import_prompt: str = DEFAULT_IMPORT_PROMPT,
    import_story: str = DEFAULT_IMPORT_STORY,
    import_owner: str = DEFAULT_IMPORT_OWNER,
) -> str:
    _, clean_space_url, clean_pack_url, clean_pack_sha1, clean_gallery_world = server_config_yaml(
        space_url,
        resource_pack_url,
        resource_pack_sha1,
        gallery_world,
        offer_pack_on_join,
        import_prompt,
        import_story,
        import_owner,
    )
    clean_import_prompt = clean_text(import_prompt, DEFAULT_IMPORT_PROMPT)
    clean_import_story = clean_text(import_story, DEFAULT_IMPORT_STORY)
    clean_import_owner = clean_text(import_owner, DEFAULT_IMPORT_OWNER)
    profile = server_owner_profile_manifest(
        clean_space_url,
        clean_pack_url,
        clean_pack_sha1,
        clean_gallery_world,
        clean_import_prompt,
        clean_import_story,
        clean_import_owner,
    )
    upload_rows = "\n".join(
        f"""
        <li>
          <code>{html_escape(row['kit_path'])}</code>
          <span>{html_escape(row['server_path'])}</span>
        </li>
        """
        for row in profile["upload_map"]
    )
    commands = "".join(f"<code>{html_escape(command)}</code>" for command in profile["first_run_commands"])
    verify = "".join(f"<code>{html_escape(command)}</code>" for command in profile["verification_commands"])
    return f"""
    <section class="server-owner-card">
      <header>
        <div>
          <span>Server owner install card</span>
          <h3>{html_escape(clean_gallery_world)} / AfterBlock Museum</h3>
        </div>
        <b>{CANVAS_SIZE * CANVAS_SIZE} plots</b>
      </header>
      <div class="server-owner-grid">
        <article>
          <span>Space endpoint</span>
          <code>{html_escape(profile['space']['quick_curate_endpoint'])}</code>
        </article>
        <article>
          <span>Resource pack SHA1</span>
          <code>{html_escape(clean_pack_sha1)}</code>
        </article>
        <article>
          <span>Default relic</span>
          <strong>{html_escape(clean_import_prompt)}</strong>
          <p>{html_escape(clean_import_story)}</p>
          <em>{html_escape(clean_import_owner)}</em>
        </article>
      </div>
      <div class="server-owner-columns">
        <div>
          <h4>Upload map</h4>
          <ol>{upload_rows}</ol>
        </div>
        <div>
          <h4>Run in Minecraft</h4>
          <div class="server-owner-command-strip">{commands}</div>
          <h4>Verify</h4>
          <div class="server-owner-command-strip">{verify}</div>
        </div>
      </div>
      <p class="server-owner-note">Download the complete Paper server kit ZIP below. It includes this card as <code>afterblock-server-profile.json</code>, plus <code>UPLOAD_TO_SERVER.md</code> and <code>install-afterblock-paper.sh</code>; it does not contain any server panel or SFTP secret.</p>
    </section>
    """


def server_upload_guide_md(
    clean_space_url: str,
    clean_pack_url: str,
    clean_pack_sha1: str,
    clean_gallery_world: str,
) -> str:
    return f"""# Upload AfterBlock to a Paper Server

This public kit is safe to share. It contains the Paper plugin, config, resource pack, demo proof files, and a helper script, but no server secret.

## Upload Map

```text
plugins/dreamwall-paper-bridge-0.1.0.jar -> plugins/dreamwall-paper-bridge-0.1.0.jar
plugins/DreamWall/config.yml -> plugins/DreamWall/config.yml
AfterBlockMuseum.zip -> AfterBlockMuseum.zip
afterblock-demo-world.zip -> afterblock-demo-world.zip
server.properties.append -> optional server.properties reference
```

The resource pack can also stay hosted here:

```text
{clean_pack_url}
sha1={clean_pack_sha1}
```

## File Manager Path

If your host has a web file manager, upload the files above, restart Paper, then run the Minecraft commands below as an op player.

## SFTP Helper

From this ZIP folder, run:

```bash
AFTERBLOCK_SFTP_HOST="your-sftp-host" \\
AFTERBLOCK_SFTP_PORT="2222" \\
AFTERBLOCK_SFTP_USER="your-sftp-user" \\
sh install-afterblock-paper.sh
```

`AFTERBLOCK_SERVER_ROOT` is optional and defaults to `.`.

## Minecraft First Run

```text
/dreamwall pack
/dreamwall museum build
/dreamwall museum check
/dreamwall import
```

Fast nearby proof:

```text
/dreamwall import here
```

Expected proof in `{clean_gallery_world}`:

```text
144 plot pads
YOU ARE HERE beacon
route compass from entry to the generated plot
engraved nameplate, passport lectern, profile button, and CustomModelData item
```

Space endpoint:

```text
{clean_space_url}/gradio_api/call/quick_curate
```
"""


def server_upload_helper_sh() -> str:
    return """#!/usr/bin/env sh
set -eu

ROOT="${AFTERBLOCK_SERVER_ROOT:-.}"
HOST="${AFTERBLOCK_SFTP_HOST:-}"
PORT="${AFTERBLOCK_SFTP_PORT:-22}"
USER_NAME="${AFTERBLOCK_SFTP_USER:-}"

required_files="
plugins/dreamwall-paper-bridge-0.1.0.jar
plugins/DreamWall/config.yml
AfterBlockMuseum.zip
afterblock-demo-world.zip
afterblock-demo-proof.json
afterblock-server-profile.json
server.properties.append
"

echo "AfterBlock Paper server kit"
echo

missing=0
for file in $required_files; do
  if [ ! -e "$file" ]; then
    echo "Missing: $file"
    missing=1
  fi
done

if [ "$missing" -ne 0 ]; then
  echo
  echo "Run this script from the unzipped afterblock-paper-server-kit folder."
  exit 1
fi

cat <<'MAP'
Upload map:
  plugins/dreamwall-paper-bridge-0.1.0.jar -> plugins/dreamwall-paper-bridge-0.1.0.jar
  plugins/DreamWall/config.yml -> plugins/DreamWall/config.yml
  AfterBlockMuseum.zip -> AfterBlockMuseum.zip
  afterblock-demo-world.zip -> afterblock-demo-world.zip

After restart, run in Minecraft:
  /dreamwall pack
  /dreamwall museum build
  /dreamwall museum check
  /dreamwall import
  /dreamwall import here
MAP

if [ -z "$HOST" ] || [ -z "$USER_NAME" ]; then
  cat <<'ENV'

No SFTP target was provided, so nothing was uploaded.
To run the guided upload, set AFTERBLOCK_SFTP_HOST and AFTERBLOCK_SFTP_USER:

  AFTERBLOCK_SFTP_HOST="your-sftp-host" AFTERBLOCK_SFTP_PORT="2222" AFTERBLOCK_SFTP_USER="your-sftp-user" sh install-afterblock-paper.sh

ENV
  exit 0
fi

batch_file="${TMPDIR:-/tmp}/afterblock-sftp-batch.$$"
trap 'rm -f "$batch_file"' EXIT

cat > "$batch_file" <<EOF
-mkdir ${ROOT}/plugins
-mkdir ${ROOT}/plugins/DreamWall
put plugins/dreamwall-paper-bridge-0.1.0.jar ${ROOT}/plugins/dreamwall-paper-bridge-0.1.0.jar
put plugins/DreamWall/config.yml ${ROOT}/plugins/DreamWall/config.yml
put AfterBlockMuseum.zip ${ROOT}/AfterBlockMuseum.zip
put afterblock-demo-world.zip ${ROOT}/afterblock-demo-world.zip
put afterblock-demo-proof.json ${ROOT}/afterblock-demo-proof.json
put afterblock-server-profile.json ${ROOT}/afterblock-server-profile.json
put server.properties.append ${ROOT}/server.properties.append
EOF

echo
echo "Opening SFTP batch for $USER_NAME@$HOST:$PORT"
sftp -P "$PORT" -b "$batch_file" "$USER_NAME@$HOST"
"""


def server_config_zip(
    space_url: str = PUBLIC_SPACE_URL,
    resource_pack_url: str = RESOURCE_PACK_URL,
    resource_pack_sha1: str = RESOURCE_PACK_SHA1,
    gallery_world: str = "world",
    offer_pack_on_join: bool = False,
    import_prompt: str = DEFAULT_IMPORT_PROMPT,
    import_story: str = DEFAULT_IMPORT_STORY,
    import_owner: str = DEFAULT_IMPORT_OWNER,
) -> str:
    config, clean_space_url, clean_pack_url, clean_pack_sha1, clean_gallery_world = server_config_yaml(
        space_url,
        resource_pack_url,
        resource_pack_sha1,
        gallery_world,
        offer_pack_on_join,
        import_prompt,
        import_story,
        import_owner,
    )
    clean_import_prompt = clean_text(import_prompt, DEFAULT_IMPORT_PROMPT)
    clean_import_story = clean_text(import_story, DEFAULT_IMPORT_STORY)
    clean_import_owner = clean_text(import_owner, DEFAULT_IMPORT_OWNER)
    proof_manifest = server_demo_proof_manifest(
        clean_space_url,
        clean_pack_url,
        clean_pack_sha1,
        clean_gallery_world,
        clean_import_prompt,
        clean_import_story,
        clean_import_owner,
    )
    owner_profile = server_owner_profile_manifest(
        clean_space_url,
        clean_pack_url,
        clean_pack_sha1,
        clean_gallery_world,
        clean_import_prompt,
        clean_import_story,
        clean_import_owner,
    )
    kit_dir = tempfile.mkdtemp(prefix="afterblock-server-kit-")
    zip_path = os.path.join(kit_dir, "afterblock-paper-server-kit.zip")
    readme = f"""# AfterBlock Paper Server Kit

This kit configures a Paper server as a persistent AfterBlock Museum for:

{clean_space_url}

## Upload

This ZIP is self-contained for the server side:

1. Upload `plugins/dreamwall-paper-bridge-0.1.0.jar` to the server's `plugins/` folder.
2. Upload `AfterBlockMuseum.zip` to the server root, or use the hosted pack URL below.
3. Upload `plugins/DreamWall/config.yml` to the same path on the server.
4. Optional: unzip `afterblock-demo-world.zip` into the server root before restart for a prebuilt memory-spine base. Run `/dreamwall museum build` once after restart to refresh the latest entry atlas.
5. Restart Paper.

## First Run

```text
/dreamwall pack
/dreamwall museum build
/dreamwall museum check
/dreamwall import
```

Use `/dreamwall import here` for a fast nearby proof during recording.

`/dreamwall import` uses the configured default relic:

```text
prompt={clean_import_prompt}
story={clean_import_story}
owner={clean_import_owner}
```

## Coordinate Contract

```text
world_x = {GALLERY_ORIGIN_X} + plot_x * {PLOT_SCALE}
world_y = {GALLERY_ORIGIN_Y}
world_z = {GALLERY_ORIGIN_Z} + plot_z * {PLOT_SCALE}
world = {clean_gallery_world}
```

## Resource Pack

```text
{clean_pack_url}
sha1={clean_pack_sha1}
```

## Included Files

```text
plugins/dreamwall-paper-bridge-0.1.0.jar
plugins/DreamWall/config.yml
AfterBlockMuseum.zip
afterblock-demo-world.zip
afterblock-demo-proof.json
afterblock-server-profile.json
UPLOAD_TO_SERVER.md
install-afterblock-paper.sh
server.properties.append
README.md
```

## Server Owner Profile

`afterblock-server-profile.json` is the shareable install card for a server owner. It includes the configured Space URL, world, resource pack, default relic, upload map, first-run commands, verification commands, and helper file names without storing any panel or SFTP secret.

## Upload Helper

`UPLOAD_TO_SERVER.md` gives the file-manager path and the exact first-run Minecraft commands.
`install-afterblock-paper.sh` can create and run an SFTP batch when `AFTERBLOCK_SFTP_HOST` and `AFTERBLOCK_SFTP_USER` are set; otherwise it only prints the upload map.

## Demo Proof File

`afterblock-demo-proof.json` is included for judges and future installers. It records the Space endpoint, default relic, coordinate contract, expected `/dreamwall museum check` proof, resource-pack counts, checksums, and the one external blocker: PebbleHost upload still needs the panel/SFTP password.

## Checksums

```text
dreamwall-paper-bridge-0.1.0.jar sha1={PAPER_PLUGIN_SHA1}
dreamwall-paper-bridge-0.1.0.jar sha256={PAPER_PLUGIN_SHA256}
AfterBlockMuseum.zip sha1={clean_pack_sha1}
afterblock-demo-world.zip sha1={PREBUILT_WORLD_SHA1}
afterblock-demo-world.zip sha256={PREBUILT_WORLD_SHA256}
```
"""
    server_properties = f"""# Optional server.properties lines
resource-pack={clean_pack_url}
resource-pack-sha1={clean_pack_sha1}
"""
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("plugins/DreamWall/config.yml", config)
        zf.writestr("README.md", readme)
        zf.writestr("server.properties.append", server_properties)
        zf.writestr(
            "UPLOAD_TO_SERVER.md",
            server_upload_guide_md(
                clean_space_url,
                clean_pack_url,
                clean_pack_sha1,
                clean_gallery_world,
            ),
        )
        zf.writestr("install-afterblock-paper.sh", server_upload_helper_sh())
        zf.writestr("afterblock-demo-proof.json", json.dumps(proof_manifest, indent=2) + "\n")
        zf.writestr("afterblock-server-profile.json", json.dumps(owner_profile, indent=2) + "\n")
        if os.path.exists(PAPER_PLUGIN_JAR_PATH):
            zf.write(PAPER_PLUGIN_JAR_PATH, "plugins/dreamwall-paper-bridge-0.1.0.jar")
        if os.path.exists(RESOURCE_PACK_PATH):
            zf.write(RESOURCE_PACK_PATH, "AfterBlockMuseum.zip")
        if os.path.exists(PREBUILT_WORLD_PATH):
            zf.write(PREBUILT_WORLD_PATH, "afterblock-demo-world.zip")
    return zip_path


def server_config_bundle(
    space_url: str = PUBLIC_SPACE_URL,
    resource_pack_url: str = RESOURCE_PACK_URL,
    resource_pack_sha1: str = RESOURCE_PACK_SHA1,
    gallery_world: str = "world",
    offer_pack_on_join: bool = False,
    import_prompt: str = DEFAULT_IMPORT_PROMPT,
    import_story: str = DEFAULT_IMPORT_STORY,
    import_owner: str = DEFAULT_IMPORT_OWNER,
) -> tuple[str, str, str]:
    return (
        server_config_kit_text(
            space_url,
            resource_pack_url,
            resource_pack_sha1,
            gallery_world,
            offer_pack_on_join,
            import_prompt,
            import_story,
            import_owner,
        ),
        server_config_zip(
            space_url,
            resource_pack_url,
            resource_pack_sha1,
            gallery_world,
            offer_pack_on_join,
            import_prompt,
            import_story,
            import_owner,
        ),
        server_owner_install_card_html(
            space_url,
            resource_pack_url,
            resource_pack_sha1,
            gallery_world,
            offer_pack_on_join,
            import_prompt,
            import_story,
            import_owner,
        ),
    )


def social_tag_for(owner_handle: str) -> str:
    handle = (owner_handle or "").strip()
    if handle and not handle.startswith("@"):
        return f"@{handle}"
    return handle


def visitor_identity(signature: str) -> tuple[str, str]:
    raw = " ".join(str(signature or "").split())
    if not raw:
        return "Visitor", ""
    handle = next((part for part in raw.split() if part.startswith("@") and len(part) > 1), "")
    if handle:
        owner_name = raw.replace(handle, "").strip() or handle[1:]
        return owner_name, social_tag_for(handle)
    return raw, ""


def compact_text(value: str, limit: int = 34) -> str:
    value = " ".join(str(value or "").split())
    if len(value) <= limit:
        return value
    return value[: max(0, limit - 1)].rstrip() + "…"


def demo_collection_artifact(index: int) -> dict:
    base = OBJECT_LIBRARY[index % len(OBJECT_LIBRARY)]
    name, input_kind, prompt, memory, object_kind = base
    handle = SOCIAL_HANDLES[index % len(SOCIAL_HANDLES)]
    variant = index // len(OBJECT_LIBRARY)
    owner = handle.strip("@").replace("_", " ").title()
    suffixes = ["launch", "rain", "exam", "midnight", "first-room"]
    source_prompt = f"{prompt}, {suffixes[variant % len(suffixes)]} variant {variant + 1}"
    memory_text = f"{memory} Visitor echo #{index + 1}."
    artifact = build_museum_artifact(owner, handle, input_kind, source_prompt, memory_text)
    artifact["catalog_index"] = index + 1
    artifact["object_kind"] = object_kind
    artifact["texture_path"] = f"assets/afterblock_textures/items/{object_kind.replace(' ', '_')}_{index + 1:04d}.png"
    artifact["resource_pack_item"] = resource_pack_item_for(object_kind, index)
    return artifact


def texture_key_for(object_guess: str) -> str:
    key = object_guess.replace(" ", "_")
    aliases = {
        "prompted_painting": "painting",
        "personal_relic": "notebook",
        "animal_spirit": "toy_car",
        "school_bag": "school_bag",
        "water_bottle": "water_bottle",
        "usb_drive": "usb_drive",
        "phone": "phone",
        "plush_toy": "plush_toy",
        "sticker": "sticker",
        "shoes": "shoes",
    }
    return aliases.get(key, key)


def resource_manifest() -> list[dict]:
    path = "assets/afterblock_textures/afterblock_manifest.json"
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except OSError:
        return []


def resource_pack_stats() -> dict:
    manifest = resource_manifest()
    kinds = {item.get("kind", "unknown") for item in manifest}
    shapes = {item.get("shape", "unknown") for item in manifest}
    profiles = {item.get("model_profile", "legacy") for item in manifest}
    materials = {item.get("material", "untextured") for item in manifest}
    return {
        "total_items": len(manifest),
        "total_kinds": len(kinds),
        "total_shapes": len(shapes),
        "total_model_profiles": len(profiles),
        "total_materials": len(materials),
        "page_count": max(1, math.ceil(len(manifest) / TEXTURE_PAGE_SIZE)),
    }


def resource_pack_item_for(object_guess: str, seed_hint: int = 0) -> dict:
    key = texture_key_for(object_guess)
    manifest = resource_manifest()
    matches = [item for item in manifest if item.get("kind") == key]
    if not matches:
        matches = [item for item in manifest if item.get("kind") == "notebook"] or manifest
    if not matches:
        return {
            "id": "missing",
            "custom_model_data": 0,
            "texture": "",
            "model": "",
            "recommended_item": "minecraft:paper",
        }
    return matches[seed_hint % len(matches)]


def texture_kind_choices() -> list[str]:
    kinds = sorted({item.get("kind", "unknown") for item in resource_manifest()})
    return ["all"] + kinds


def texture_preview_url(item_id: str) -> str:
    base = os.getenv(
        "TEXTURE_PREVIEW_BASE_URL",
        "https://raw.githubusercontent.com/Arnie016/dreamwall-mc/main/assets/afterblock_textures/gallery/previews",
    ).rstrip("/")
    if base:
        return f"{base}/{item_id}.png"
    return f"assets/afterblock_textures/gallery/previews/{item_id}.png"


def block_rgb(block_name: str) -> tuple[int, int, int]:
    return next((rgb for name, rgb in BLOCKS if name == block_name), (180, 156, 104))


def hex_color(rgb: tuple[int, int, int]) -> str:
    return "#{:02x}{:02x}{:02x}".format(*rgb)


def artifact_model_html(artifact: dict) -> str:
    item = artifact.get("resource_pack_item", {})
    item_id = item.get("id", "missing")
    hall_rgb = hall_color(artifact["hall"])
    palette = [hex_color(block_rgb(name)) for name in artifact.get("palette", [])[:5]]
    if not palette:
        palette = [hex_color(hall_rgb), "#e8c56f", "#3b3120"]
    payload = {
        "title": artifact["title"],
        "owner": owner_display(artifact),
        "hall": artifact["hall"],
        "when": artifact.get("artifact_when", artifact["placement_reason"]),
        "coordinates": artifact["minecraft_coordinates"],
        "custom_model_data": item.get("custom_model_data", 0),
        "model": item.get("model", "afterblock:item/missing"),
        "kind": item.get("kind", texture_key_for(artifact["object_guess"])),
        "object_guess": artifact["object_guess"],
        "shape": item.get("shape", artifact["object_guess"]),
        "material": item.get("material", "museum material"),
        "finish": item.get("finish", "artifact finish"),
        "profile": item.get("model_profile", "fixed pedestal"),
        "orientation": item.get("orientation", "front-facing"),
        "element_count": int(item.get("element_count") or 7),
        "preview_url": texture_preview_url(item_id) if item_id != "missing" else "",
        "colors": palette,
        "hall_color": hex_color(hall_rgb),
        "story_caption": artifact.get("memory_text", artifact.get("plaque_line", "")),
        "social_tag": artifact.get("social_tag", owner_display(artifact)),
        "give_command": f"/give @p minecraft:paper[minecraft:custom_model_data={item.get('custom_model_data', 0)}] 1",
    }
    payload_json = json.dumps(payload)
    fallback_swatches = "".join(
        f"<span style='background:{html_escape(color)}'></span>" for color in payload["colors"]
    )
    srcdoc = f"""
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<style>
  html, body {{ margin:0; height:100%; background:#10110f; color:#f8e5b6; font-family: Inter, ui-sans-serif, system-ui, sans-serif; overflow:hidden; }}
  #stage {{ position:absolute; inset:0; cursor:grab; touch-action:none; }}
  #stage.dragging {{ cursor:grabbing; }}
  .hud {{ position:absolute; left:18px; right:18px; bottom:16px; display:grid; grid-template-columns:1fr auto; gap:12px; align-items:end; pointer-events:none; }}
  .label {{ background:rgba(18,15,10,.78); border:1px solid #8c6a38; padding:12px 14px; box-shadow:0 6px 0 rgba(0,0,0,.38); }}
  h2 {{ margin:0 0 4px; font-size:18px; color:#ffe4a3; letter-spacing:.01em; }}
  p {{ margin:3px 0; font-size:12px; line-height:1.35; color:#d8c8a4; }}
  code {{ color:#20160c; background:#e8c56f; padding:4px 6px; display:inline-block; margin-top:4px; font-size:11px; }}
  .badge {{ border:1px solid #7d6335; color:#ffe4a3; padding:8px 10px; background:rgba(28,24,18,.8); font-weight:800; font-size:12px; }}
  .fallback {{ position:absolute; inset:0; display:grid; place-items:center; background:radial-gradient(circle at 50% 35%, rgba(220,172,88,.16), transparent 42%), #10110f; }}
  .fallback-card {{ width:150px; height:150px; transform:rotateX(58deg) rotateZ(-28deg); background:linear-gradient(135deg, {html_escape(payload['hall_color'])}, #ffe3a1); border:8px solid #1d160d; box-shadow:34px 28px 0 rgba(0,0,0,.34); }}
  .swatches {{ display:flex; gap:4px; margin-top:7px; }}
  .swatches span {{ width:16px; height:16px; border:1px solid #0e0c09; }}
</style>
</head>
<body>
<div id="stage"></div>
<div id="fallback" class="fallback"><div><div class="fallback-card"></div><div class="swatches">{fallback_swatches}</div></div></div>
<div class="hud">
  <div class="label">
    <h2 id="title"></h2>
    <p id="meta"></p>
    <p id="when"></p>
    <code id="cmd"></code>
  </div>
  <div class="badge" id="badge"></div>
</div>
<script type="module">
  import * as THREE from 'https://esm.sh/three@0.160.0';
  const artifact = {payload_json};
  document.getElementById('title').textContent = artifact.title;
  document.getElementById('meta').textContent = `${{artifact.owner}} · ${{artifact.hall}} · ${{artifact.material}} · ${{artifact.profile}}`;
  document.getElementById('when').textContent = `When: ${{artifact.when}} · XYZ ${{artifact.coordinates.x}} ${{artifact.coordinates.y}} ${{artifact.coordinates.z}}`;
  document.getElementById('cmd').textContent = artifact.give_command;
  document.getElementById('badge').textContent = `CMD ${{artifact.custom_model_data}}`;

  const stage = document.getElementById('stage');
  const scene = new THREE.Scene();
  scene.background = new THREE.Color('#0d0f0e');
  const camera = new THREE.PerspectiveCamera(38, stage.clientWidth / stage.clientHeight, 0.1, 100);
  camera.position.set(3.9, 3.1, 5.1);
  camera.lookAt(0, .7, 0);
  let cameraDistance = 5.1;

  const renderer = new THREE.WebGLRenderer({{ antialias: true, alpha: true }});
  renderer.setSize(stage.clientWidth, stage.clientHeight);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  renderer.shadowMap.enabled = true;
  stage.appendChild(renderer.domElement);
  document.getElementById('fallback').style.display = 'none';

  scene.add(new THREE.HemisphereLight('#fff1c8', '#15120d', 2.1));
  const key = new THREE.DirectionalLight('#ffe0a3', 2.4);
  key.position.set(3, 5, 4);
  key.castShadow = true;
  scene.add(key);
  const rim = new THREE.PointLight(artifact.hall_color, 12, 7);
  rim.position.set(-2.2, 2.5, -1.4);
  scene.add(rim);

  const group = new THREE.Group();
  scene.add(group);
  const hallGroup = new THREE.Group();
  scene.add(hallGroup);
  const colors = artifact.colors.length ? artifact.colors : [artifact.hall_color, '#e8c56f'];
  const materialFor = (i) => new THREE.MeshStandardMaterial({{
    color: new THREE.Color(colors[i % colors.length]),
    roughness: .72,
    metalness: artifact.material.includes('metal') || artifact.material.includes('brass') ? .35 : .05,
    emissive: artifact.material.includes('glow') || artifact.finish.includes('glow') ? new THREE.Color(colors[i % colors.length]).multiplyScalar(.18) : new THREE.Color('#000000')
  }});
  const dark = new THREE.MeshStandardMaterial({{ color:'#17120b', roughness:.9 }});
  const makeMat = (color, options = {{}}) => new THREE.MeshStandardMaterial({{
    color,
    roughness: options.roughness ?? .68,
    metalness: options.metalness ?? 0,
    emissive: options.emissive ? new THREE.Color(options.emissive).multiplyScalar(options.emissiveStrength ?? .16) : new THREE.Color('#000000')
  }});

  function cube(x, y, z, sx, sy, sz, mat) {{
    const mesh = new THREE.Mesh(new THREE.BoxGeometry(sx, sy, sz), mat);
    mesh.position.set(x, y, z);
    mesh.castShadow = true;
    mesh.receiveShadow = true;
    group.add(mesh);
    return mesh;
  }}

  function hallCube(x, y, z, sx, sy, sz, mat) {{
    const mesh = new THREE.Mesh(new THREE.BoxGeometry(sx, sy, sz), mat);
    mesh.position.set(x, y, z);
    mesh.castShadow = true;
    mesh.receiveShadow = true;
    hallGroup.add(mesh);
    return mesh;
  }}

  function buildMuseumHall() {{
    const floor = makeMat('#211d16', {{ roughness: .88 }});
    const tileA = makeMat('#31291d', {{ roughness: .86 }});
    const tileB = makeMat('#171410', {{ roughness: .9 }});
    const wall = makeMat('#2a2118', {{ roughness: .92 }});
    const trim = makeMat('#7a5729', {{ roughness: .72, metalness: .08 }});
    const portalDark = makeMat('#0a0908', {{ roughness: .95, emissive: '#1d1234', emissiveStrength: .08 }});
    const lamp = makeMat('#ffd47d', {{ roughness: .34, emissive: '#ffb84a', emissiveStrength: .55 }});
    const blueHall = makeMat('#315f87', {{ roughness: .72, emissive: '#1a5f86', emissiveStrength: .08 }});
    const greenHall = makeMat('#335f3a', {{ roughness: .72, emissive: '#2c6d39', emissiveStrength: .08 }});
    const violetHall = makeMat('#442264', {{ roughness: .72, emissive: '#4b1689', emissiveStrength: .1 }});

    hallCube(0, -.08, .15, 7.6, .14, 5.9, floor);
    for (let x = -3; x <= 3; x++) {{
      for (let z = -2; z <= 2; z++) {{
        hallCube(x * .92, -.005, z * .82, .82, .035, .72, (x + z) % 2 ? tileA : tileB);
      }}
    }}

    hallCube(0, 1.25, -2.62, 7.6, 2.55, .22, wall);
    hallCube(-3.86, 1.0, .1, .22, 2.0, 5.7, wall);
    hallCube(3.86, 1.0, .1, .22, 2.0, 5.7, wall);
    hallCube(0, .04, -2.02, 5.8, .09, .18, trim);
    hallCube(0, .04, 2.44, 5.6, .09, .18, trim);

    const portals = [
      [-2.35, -2.48, 'Worlds', blueHall],
      [0, -2.49, 'Companions', greenHall],
      [2.35, -2.48, 'Turning', violetHall],
    ];
    portals.forEach(([x, z, name, mat], index) => {{
      hallCube(x, .92, z, .88, 1.45, .18, portalDark);
      hallCube(x - .54, .92, z + .03, .16, 1.55, .24, trim);
      hallCube(x + .54, .92, z + .03, .16, 1.55, .24, trim);
      hallCube(x, 1.68, z + .03, 1.24, .18, .24, trim);
      hallCube(x, 1.92, z + .08, 1.04, .22, .16, mat);
      hallCube(x - .72, 1.36, z + .12, .12, .32, .12, lamp);
      hallCube(x + .72, 1.36, z + .12, .12, .32, .12, lamp);
    }});

    const sideCases = [
      [-2.75, .42, .95, '#6b3a2f'],
      [2.75, .42, .95, '#365476'],
      [-2.78, .42, 1.9, '#6a5630'],
      [2.78, .42, 1.9, '#4b6537'],
    ];
    sideCases.forEach(([x, y, z, color], i) => {{
      hallCube(x, .2, z, .88, .25, .68, trim);
      hallCube(x, .65, z, .42, .46, .28, makeMat(color, {{ roughness: .62, emissive: color, emissiveStrength: .04 }}));
      hallCube(x, 1.02, z, .72, .1, .38, lamp);
    }});

    hallCube(0, .05, 0, 3.0, .1, 2.18, dark);
    hallCube(0, .23, 0, 2.2, .24, 1.5, new THREE.MeshStandardMaterial({{ color:'#4a371d', roughness:.85 }}));
    hallCube(0, .43, -.83, 1.35, .16, .2, trim);
    hallCube(0, .78, -.88, 1.1, .58, .12, makeMat('#1a130c', {{ roughness: .8 }}));
  }}

  buildMuseumHall();

  function labelTexture(title, caption) {{
    const canvas = document.createElement('canvas');
    canvas.width = 512;
    canvas.height = 192;
    const ctx = canvas.getContext('2d');
    ctx.fillStyle = '#1a1209';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.strokeStyle = '#c99b4e';
    ctx.lineWidth = 10;
    ctx.strokeRect(10, 10, canvas.width - 20, canvas.height - 20);
    ctx.fillStyle = '#ffe4a3';
    ctx.font = 'bold 32px Inter, system-ui, sans-serif';
    ctx.fillText(String(title || 'Relic').slice(0, 24), 34, 58);
    ctx.fillStyle = '#e7d5ad';
    ctx.font = '22px ui-monospace, SFMono-Regular, Menlo, monospace';
    const words = String(caption || '').split(/\\s+/).slice(0, 18);
    let line = '';
    let y = 96;
    words.forEach((word) => {{
      const test = line ? `${{line}} ${{word}}` : word;
      if (ctx.measureText(test).width > 440) {{
        ctx.fillText(line, 34, y);
        line = word;
        y += 30;
      }} else {{
        line = test;
      }}
    }});
    if (line) ctx.fillText(line, 34, y);
    const texture = new THREE.CanvasTexture(canvas);
    texture.colorSpace = THREE.SRGBColorSpace;
    return texture;
  }}

  function buildEngravedPlaque() {{
    const plaqueTexture = labelTexture(artifact.title, artifact.story_caption);
    const plaque = new THREE.Mesh(
      new THREE.PlaneGeometry(1.34, .5),
      new THREE.MeshBasicMaterial({{ map: plaqueTexture, transparent: false }})
    );
    plaque.position.set(0, .86, -.955);
    plaque.rotation.x = 0;
    hallGroup.add(plaque);
  }}

  buildEngravedPlaque();

  const shapeText = `${{artifact.kind}} ${{artifact.shape}} ${{artifact.object_guess}} ${{artifact.title}}`.toLowerCase();
  const ivory = makeMat('#f5efdc', {{ roughness: .42 }});
  const porcelain = makeMat('#fff9e8', {{ roughness: .35 }});
  const blueGlow = makeMat('#6fd3ff', {{ roughness: .28, emissive: '#6fd3ff', emissiveStrength: .18 }});
  const graphite = makeMat('#171a1c', {{ roughness: .72 }});
  const screenBlue = makeMat('#1d8fd1', {{ roughness: .25, emissive: '#1b6fa8', emissiveStrength: .18 }});
  const rubber = makeMat('#2b2722', {{ roughness: .9 }});

  function renderEarbuds() {{
    cube(-.36, .72, -.02, .15, .72, .14, ivory);
    cube(.36, .72, -.02, .15, .72, .14, ivory);
    cube(-.36, 1.16, -.04, .32, .25, .24, porcelain);
    cube(.36, 1.16, -.04, .32, .25, .24, porcelain);
    cube(-.47, 1.18, -.18, .1, .07, .05, graphite);
    cube(.25, 1.18, -.18, .1, .07, .05, graphite);
    cube(-.36, .39, .08, .1, .13, .18, blueGlow);
    cube(.36, .39, .08, .1, .13, .18, blueGlow);
  }}

  function renderMonitor() {{
    cube(0, 1.05, -.02, 1.56, .9, .14, graphite);
    cube(0, 1.05, -.11, 1.38, .72, .08, screenBlue);
    cube(0, .5, .02, .18, .55, .18, graphite);
    cube(0, .28, .02, .84, .14, .44, graphite);
  }}

  function renderClock() {{
    cube(0, .92, -.02, .96, .96, .16, ivory);
    cube(0, .92, -.13, .78, .78, .06, porcelain);
    cube(0, .92, -.18, .07, .36, .05, graphite);
    cube(.16, .82, -.18, .32, .07, .05, graphite);
    cube(-.28, 1.46, -.02, .18, .18, .16, blueGlow);
    cube(.28, 1.46, -.02, .18, .18, .16, blueGlow);
    cube(0, .34, .02, .82, .16, .28, rubber);
  }}

  function renderShoes() {{
    cube(-.38, .45, -.02, .62, .22, .42, rubber);
    cube(.38, .45, -.02, .62, .22, .42, rubber);
    cube(-.33, .62, -.04, .48, .28, .32, materialFor(0));
    cube(.43, .62, -.04, .48, .28, .32, materialFor(1));
    cube(-.1, .74, -.18, .28, .08, .08, ivory);
    cube(.66, .74, -.18, .28, .08, .08, ivory);
  }}

  function renderRemote() {{
    cube(0, .83, -.02, .48, 1.38, .18, graphite);
    cube(0, 1.38, -.14, .18, .14, .06, makeMat('#e85b4d', {{ roughness: .48 }}));
    for (let r = 0; r < 4; r++) {{
      for (let c = 0; c < 2; c++) {{
        cube((c - .5) * .18, 1.08 - r * .18, -.14, .1, .08, .06, c === 0 ? blueGlow : ivory);
      }}
    }}
    cube(0, .38, -.14, .28, .16, .06, makeMat('#70685a', {{ roughness: .72 }}));
  }}

  function renderBag() {{
    const body = makeMat('#334f86', {{ roughness: .82 }});
    const panel = makeMat('#5f78b8', {{ roughness: .72 }});
    const strap = makeMat('#1a2131', {{ roughness: .9 }});
    const zip = makeMat('#f3d77d', {{ roughness: .45, metalness: .12 }});
    cube(0, .86, -.02, 1.0, 1.08, .42, body);
    cube(0, .9, -.26, .74, .74, .1, panel);
    cube(-.38, 1.42, -.04, .16, .38, .18, strap);
    cube(.38, 1.42, -.04, .16, .38, .18, strap);
    cube(0, 1.36, -.29, .56, .08, .06, zip);
    cube(0, .54, -.31, .5, .14, .08, makeMat('#28375b', {{ roughness: .8 }}));
    cube(-.57, .86, .02, .12, .88, .3, strap);
    cube(.57, .86, .02, .12, .88, .3, strap);
  }}

  function renderPhone() {{
    const shell = makeMat('#14181d', {{ roughness: .54, metalness: .22 }});
    const glass = makeMat('#102431', {{ roughness: .18, metalness: .08, emissive: '#2fb6ff', emissiveStrength: .16 }});
    const bezel = makeMat('#0a0b0d', {{ roughness: .72 }});
    const appA = makeMat('#6fd3ff', {{ roughness: .3, emissive: '#40b9ff', emissiveStrength: .2 }});
    const appB = makeMat('#f4d76f', {{ roughness: .36, emissive: '#f4c44a', emissiveStrength: .09 }});
    const appC = makeMat('#7fe0a3', {{ roughness: .36, emissive: '#42c36f', emissiveStrength: .1 }});
    const appD = makeMat('#f06f6f', {{ roughness: .36, emissive: '#cf4a4a', emissiveStrength: .08 }});
    const frame = cube(0, .94, -.02, .82, 1.42, .16, shell);
    const screen = cube(0, .94, -.135, .68, 1.2, .055, glass);
    frame.rotation.z = -.03;
    screen.rotation.z = -.03;
    cube(0, 1.58, -.18, .22, .035, .04, porcelain).rotation.z = -.03;
    cube(.28, 1.43, -.19, .06, .06, .04, blueGlow).rotation.z = -.03;
    cube(-.26, .37, -.19, .22, .045, .04, bezel).rotation.z = -.03;
    cube(-.44, 1.05, -.02, .035, .34, .06, shell).rotation.z = -.03;
    cube(.44, .92, -.02, .035, .24, .06, shell).rotation.z = -.03;
    const apps = [appA, appB, appC, appD, appC, appA];
    apps.forEach((mat, i) => {{
      const col = i % 2;
      const row = Math.floor(i / 2);
      const icon = cube((col - .5) * .28, 1.18 - row * .24, -.19, .16, .13, .038, mat);
      icon.rotation.z = -.03;
    }});
    const shine = cube(-.2, 1.1, -.205, .055, .76, .03, makeMat('#d8f4ff', {{ roughness: .16, emissive: '#d8f4ff', emissiveStrength: .08 }}));
    shine.rotation.z = -.22;
  }}

  function renderWaterBottle() {{
    const bottleGlass = new THREE.MeshStandardMaterial({{
      color: '#7fd9f4',
      roughness: .18,
      metalness: .02,
      transparent: true,
      opacity: .72,
      emissive: new THREE.Color('#2f91bb').multiplyScalar(.08)
    }});
    const label = makeMat('#f4f0de', {{ roughness: .38 }});
    const cap = makeMat('#2f6f95', {{ roughness: .5, metalness: .04 }});
    const water = makeMat('#2da8d8', {{ roughness: .22, emissive: '#0b83b4', emissiveStrength: .12 }});
    const seam = makeMat('#d9fbff', {{ roughness: .18, emissive: '#bdf3ff', emissiveStrength: .08 }});
    cube(0, .62, 0, .5, .44, .38, bottleGlass);
    cube(0, .96, 0, .58, .48, .44, bottleGlass);
    cube(0, 1.3, 0, .46, .3, .36, bottleGlass);
    cube(0, .74, -.24, .48, .28, .04, water);
    cube(0, 1.0, -.27, .62, .25, .05, label);
    cube(-.19, 1.01, -.305, .06, .16, .035, cap);
    cube(.19, 1.01, -.305, .06, .16, .035, cap);
    cube(0, 1.53, 0, .28, .24, .28, bottleGlass);
    cube(0, 1.72, 0, .38, .16, .38, cap);
    cube(-.31, 1.0, -.02, .045, 1.02, .05, seam);
    cube(.31, 1.0, -.02, .045, 1.02, .05, seam);
    cube(.16, .42, -.23, .08, .1, .04, blueGlow);
  }}

  function renderPlushToy() {{
    const fur = makeMat('#9a6a43', {{ roughness: .92 }});
    const belly = makeMat('#d3ad78', {{ roughness: .88 }});
    const face = makeMat('#f1c98b', {{ roughness: .88 }});
    const innerEar = makeMat('#e8bd82', {{ roughness: .86 }});
    const bow = makeMat('#b83a31', {{ roughness: .55, emissive: '#7d1712', emissiveStrength: .05 }});
    cube(0, .7, 0, .74, .76, .5, fur);
    cube(0, .68, -.29, .42, .42, .05, belly);
    cube(0, 1.23, -.02, .62, .55, .44, fur);
    cube(-.38, 1.52, -.02, .26, .25, .2, fur);
    cube(.38, 1.52, -.02, .26, .25, .2, fur);
    cube(-.38, 1.52, -.15, .13, .12, .05, innerEar);
    cube(.38, 1.52, -.15, .13, .12, .05, innerEar);
    cube(0, 1.14, -.28, .36, .25, .07, face);
    cube(-.12, 1.27, -.33, .055, .055, .04, graphite);
    cube(.12, 1.27, -.33, .055, .055, .04, graphite);
    cube(0, 1.15, -.34, .07, .055, .04, graphite);
    cube(-.05, 1.06, -.34, .13, .035, .04, graphite);
    cube(.05, 1.06, -.34, .13, .035, .04, graphite);
    const leftArm = cube(-.56, .76, -.02, .24, .5, .3, fur);
    const rightArm = cube(.56, .76, -.02, .24, .5, .3, fur);
    leftArm.rotation.z = .18;
    rightArm.rotation.z = -.18;
    const leftLeg = cube(-.24, .25, .04, .26, .34, .3, fur);
    const rightLeg = cube(.24, .25, .04, .26, .34, .3, fur);
    leftLeg.rotation.x = -.08;
    rightLeg.rotation.x = -.08;
    cube(-.09, .99, -.32, .18, .11, .055, bow);
    cube(.09, .99, -.32, .18, .11, .055, bow);
    cube(0, .99, -.34, .07, .13, .06, makeMat('#f3d77d', {{ roughness: .5, metalness: .08 }}));
  }}

  function renderSticker() {{
    const paper = makeMat('#f4efe0', {{ roughness: .36 }});
    const inkA = makeMat(colors[0] || '#4d78ff', {{ roughness: .42, emissive: colors[0] || '#4d78ff', emissiveStrength: .05 }});
    const inkB = makeMat(colors[1] || '#77d7a8', {{ roughness: .42, emissive: colors[1] || '#77d7a8', emissiveStrength: .05 }});
    cube(0, .9, -.02, 1.05, .82, .08, paper);
    cube(-.22, .92, -.09, .34, .34, .04, inkA);
    cube(.16, .98, -.1, .42, .16, .04, inkB);
    cube(.24, .73, -.1, .32, .12, .04, graphite);
    cube(-.36, .58, -.1, .2, .12, .04, makeMat('#ffdc8a', {{ roughness: .38 }}));
  }}

  function renderGeneric() {{
    const count = Math.max(5, Math.min(14, artifact.element_count || 7));
    for (let i = 0; i < count; i++) {{
      const row = Math.floor(i / 4);
      const col = i % 4;
      const sx = .42 + (i % 3) * .08;
      const sy = .26 + ((i + row) % 4) * .12;
      const sz = .34 + (row % 3) * .08;
      const x = (col - 1.5) * .48;
      const z = (row - 1.0) * .42;
      const y = .42 + sy / 2 + Math.sin(i * 1.7) * .02;
      const part = cube(x, y, z, sx, sy, sz, materialFor(i));
      part.rotation.y = (i % 2 ? .12 : -.18);
    }}
  }}

  if (shapeText.includes('earbud') || shapeText.includes('airpod')) {{
    renderEarbuds();
  }} else if (shapeText.includes('monitor') || shapeText.includes('screen')) {{
    renderMonitor();
  }} else if (shapeText.includes('clock')) {{
    renderClock();
  }} else if (shapeText.includes('shoe')) {{
    renderShoes();
  }} else if (shapeText.includes('bag') || shapeText.includes('backpack')) {{
    renderBag();
  }} else if (shapeText.includes('phone') || shapeText.includes('smartphone') || shapeText.includes('mobile')) {{
    renderPhone();
  }} else if (shapeText.includes('bottle') || shapeText.includes('water')) {{
    renderWaterBottle();
  }} else if (shapeText.includes('plush') || shapeText.includes('teddy') || shapeText.includes('bear')) {{
    renderPlushToy();
  }} else if (shapeText.includes('sticker') || shapeText.includes('decal') || shapeText.includes('logo')) {{
    renderSticker();
  }} else if (shapeText.includes('remote')) {{
    renderRemote();
  }} else {{
    renderGeneric();
  }}
  const grid = new THREE.GridHelper(7.4, 14, artifact.hall_color, '#3a3020');
  grid.position.y = 0;
  scene.add(grid);

  let targetYaw = -.4;
  let targetPitch = .05;
  let dragging = false;
  let lastX = 0;
  let lastY = 0;

  function positionCamera() {{
    camera.position.set(
      Math.sin(targetYaw) * cameraDistance,
      2.7 + Math.sin(targetPitch) * 1.2,
      Math.cos(targetYaw) * cameraDistance
    );
    camera.lookAt(0, .72, 0);
  }}

  stage.addEventListener('pointerdown', (event) => {{
    dragging = true;
    stage.classList.add('dragging');
    lastX = event.clientX;
    lastY = event.clientY;
    stage.setPointerCapture(event.pointerId);
  }});
  stage.addEventListener('pointermove', (event) => {{
    if (!dragging) return;
    const dx = event.clientX - lastX;
    const dy = event.clientY - lastY;
    targetYaw += dx * .008;
    targetPitch = Math.max(-.8, Math.min(.65, targetPitch + dy * .006));
    lastX = event.clientX;
    lastY = event.clientY;
    positionCamera();
  }});
  stage.addEventListener('pointerup', (event) => {{
    dragging = false;
    stage.classList.remove('dragging');
    try {{ stage.releasePointerCapture(event.pointerId); }} catch (error) {{}}
  }});
  stage.addEventListener('pointerleave', () => {{
    dragging = false;
    stage.classList.remove('dragging');
  }});
  stage.addEventListener('wheel', (event) => {{
    event.preventDefault();
    cameraDistance = Math.max(3.2, Math.min(7.4, cameraDistance + event.deltaY * .003));
    positionCamera();
  }}, {{ passive: false }});
  positionCamera();

  function tick(t) {{
    group.rotation.y = dragging ? targetYaw * .08 : Math.sin(t * .00045) * .12 - .2;
    group.position.y = Math.sin(t * .0012) * .035;
    renderer.render(scene, camera);
    requestAnimationFrame(tick);
  }}
  requestAnimationFrame(tick);
  window.addEventListener('resize', () => {{
    camera.aspect = stage.clientWidth / stage.clientHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(stage.clientWidth, stage.clientHeight);
  }});
</script>
</body>
</html>
"""
    return f"""
    <section class="artifact-model-shell">
      <iframe
        title="3D Minecraft artifact model preview"
        class="artifact-model-frame"
        sandbox="allow-scripts"
        srcdoc="{html.escape(srcdoc, quote=True)}"
      ></iframe>
    </section>
    """


def texture_inspection_html(items: list[dict], total: int, page_index: int, page_count: int) -> str:
    cards = []
    for item in items:
        preview_url = texture_preview_url(item["id"])
        cards.append(
            f"""
            <article class="texture-inspect-card">
              <img src="{preview_url}" alt="{item['label']}">
              <div>
                <strong>{item['label']}</strong>
                <span>{item['kind']} · {item['shape']} · {item.get('element_count', '?')} cuboids</span>
                <span>{item.get('material', 'materialized')} · {item.get('finish', 'museum finish')}</span>
                <span>{item.get('model_profile', 'pose')} · {item.get('orientation', 'orientation')}</span>
                <code>/give @p minecraft:paper[minecraft:custom_model_data={item['custom_model_data']}] 1</code>
              </div>
            </article>
            """
        )
    return f"""
    <section class="texture-inspector">
      <header>
        <h3>Resource Pack Inspection Wall</h3>
        <p>{len(items)} visible on page {page_index}/{page_count}; {total} matching relics. Each card maps to a PNG texture, cuboid item model, material finish, pose profile, and Minecraft item code.</p>
      </header>
      <div>{''.join(cards)}</div>
    </section>
    """


def browse_texture_library(kind: str, page: int):
    manifest = resource_manifest()
    if kind and kind != "all":
        manifest = [item for item in manifest if item.get("kind") == kind]
    page_size = TEXTURE_PAGE_SIZE
    total = len(manifest)
    page_count = max(1, math.ceil(total / page_size))
    page_index = max(1, min(int(page or 1), page_count))
    start = (page_index - 1) * page_size
    items = manifest[start : start + page_size]
    gallery = [
        (
            texture_preview_url(item["id"]),
            f"{item['label']} | CMD {item['custom_model_data']}",
        )
        for item in items
    ]
    rows = [
        [
            item["custom_model_data"],
            item["label"],
            item["kind"],
            item["shape"],
            item.get("material", "untextured"),
            item.get("finish", ""),
            item.get("model_profile", "legacy"),
            item.get("orientation", "standard"),
            item.get("itemdisplay_transform", "ItemDisplay.Transform.FIXED"),
            item.get("element_count", ""),
            item["model"],
            f"/give @p minecraft:paper[minecraft:custom_model_data={item['custom_model_data']}] 1",
        ]
        for item in items
    ]
    status = (
        f"Showing {len(items)} of {total} items"
        f" | scroll shelf {page_index}/{page_count}"
        " | base item: minecraft:paper"
    )
    return gallery, rows, texture_inspection_html(items, total, page_index, page_count), status


def museum_collection(selected: dict, count: int = 100) -> list[dict]:
    artifacts = [demo_collection_artifact(i) for i in range(count)]
    selected_copy = dict(selected)
    selected_copy["catalog_index"] = 0
    selected_copy["texture_path"] = f"assets/afterblock_textures/items/{texture_key_for(selected['object_guess'])}_selected.png"
    return [selected_copy] + artifacts


def hall_color(hall: str) -> tuple[int, int, int]:
    colors = {
        "Hall of Firsts": (236, 191, 82),
        "Hall of Companions": (104, 178, 132),
        "Hall of Turning Points": (204, 114, 92),
        "Hall of Worlds": (104, 145, 214),
        "Hall of Soft Things": (222, 159, 184),
        "Hall of Tools": (151, 151, 164),
        "Hall of Lost Signals": (149, 112, 194),
        "Grand Painting Hall": (205, 132, 72),
        "Animal Spirit Grove": (111, 164, 86),
    }
    return colors.get(hall, (180, 160, 120))


def render_museum_preview(selected: dict, collection: list[dict]) -> str:
    width, height = 1600, 1040
    image = Image.new("RGB", (width, height), (13, 14, 12))
    draw = ImageDraw.Draw(image)

    def load_font(size: int):
        candidates = [
            "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/Library/Fonts/Arial.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]
        for candidate in candidates:
            try:
                return ImageFont.truetype(candidate, size=size)
            except OSError:
                continue
        return ImageFont.load_default()

    font_title = load_font(26)
    font_hall = load_font(14)
    font_body = load_font(13)
    font_tiny = load_font(10)
    pack_stats = resource_pack_stats()

    def shade(rgb: tuple[int, int, int], factor: float) -> tuple[int, int, int]:
        return tuple(max(0, min(255, int(channel * factor))) for channel in rgb)

    def iso_box(x: int, y: int, w: int, h: int, depth: int, color: tuple[int, int, int], outline: tuple[int, int, int]):
        top = [(x, y), (x + w, y), (x + w - depth, y + depth), (x + depth, y + depth)]
        left = [(x, y), (x + depth, y + depth), (x + depth, y + h + depth), (x, y + h)]
        right = [(x + w, y), (x + w - depth, y + depth), (x + w - depth, y + h + depth), (x + w, y + h)]
        face = [(x + depth, y + depth), (x + w - depth, y + depth), (x + w - depth, y + h + depth), (x + depth, y + h + depth)]
        draw.polygon(left, fill=shade(color, 0.46), outline=outline)
        draw.polygon(right, fill=shade(color, 0.55), outline=outline)
        draw.polygon(face, fill=shade(color, 0.34), outline=outline)
        draw.polygon(top, fill=shade(color, 0.78), outline=outline)

    draw.rectangle([26, 26, width - 26, height - 26], outline=(150, 112, 58), width=4)
    draw.rectangle([38, 38, width - 38, 106], fill=(29, 25, 19), outline=(94, 74, 48), width=2)
    draw.text((58, 50), "AFTERBLOCK MUSEUM", fill=(255, 225, 154), font=font_title)
    draw.text((58, 82), f"100 labeled relics - {pack_stats['total_kinds']} object families - {pack_stats['total_items']} Minecraft PNG models - live server packets", fill=(190, 176, 142), font=font_body)
    draw.text((1180, 66), "minecraft:paper + CustomModelData", fill=(211, 190, 128), font=font_body)

    # Grand floor and central sightline.
    draw.polygon([(88, 168), (1120, 168), (1040, 900), (150, 900)], fill=(32, 31, 26), outline=(92, 78, 50))
    for i in range(11):
        x0 = 120 + i * 92
        draw.line([(x0, 182), (x0 - 62, 876)], fill=(46, 43, 36), width=1)
    for j in range(8):
        y = 210 + j * 82
        draw.line([(100, y), (1110, y)], fill=(48, 44, 35), width=1)
    draw.rectangle([486, 146, 694, 910], outline=(121, 94, 55), width=3)
    draw.rectangle([520, 148, 660, 910], fill=(39, 32, 24), outline=(149, 104, 53), width=2)

    hall_positions = {
        "Hall of Firsts": (96, 142, 300, 184),
        "Hall of Companions": (370, 138, 300, 184),
        "Hall of Turning Points": (744, 142, 300, 184),
        "Hall of Worlds": (96, 382, 300, 184),
        "Hall of Soft Things": (370, 382, 300, 184),
        "Hall of Tools": (744, 382, 300, 184),
        "Hall of Lost Signals": (96, 622, 300, 184),
        "Grand Painting Hall": (370, 622, 300, 184),
        "Animal Spirit Grove": (744, 622, 300, 184),
    }

    for hall, (x, y, w, h) in hall_positions.items():
        color = hall_color(hall)
        iso_box(x, y, w, h, 24, color, shade(color, 0.9))
        draw.rectangle([x + 20, y + 30, x + w - 20, y + 54], fill=shade(color, 0.28), outline=shade(color, 0.9))
        draw.text((x + 28, y + 35), hall.upper()[:27], fill=(255, 234, 176), font=font_hall)
        for lamp in range(3):
            lx = x + 60 + lamp * 82
            draw.ellipse([lx, y + h + 16, lx + 10, y + h + 26], fill=(242, 188, 84), outline=(48, 31, 15))

    placed_counts = {hall: 0 for hall in hall_positions}
    for artifact in collection:
        hall = artifact["hall"]
        if hall not in hall_positions:
            continue
        x, y, w, h = hall_positions[hall]
        slot = placed_counts[hall]
        placed_counts[hall] += 1
        if slot >= 15:
            continue
        col = slot % 5
        row = slot // 5
        px = x + 34 + col * 50
        py = y + 72 + row * 34
        active = artifact["artifact_id"] == selected["artifact_id"]
        hall_rgb = hall_color(hall)
        artifact_rgb = (255, 232, 126) if active else shade(hall_rgb, 1.1)
        draw.rectangle([px, py + 13, px + 34, py + 22], fill=shade(artifact_rgb, 0.45), outline=(22, 19, 15))
        draw.rectangle([px + 4, py, px + 30, py + 16], fill=artifact_rgb, outline=(18, 15, 10))
        draw.rectangle([px + 8, py + 4, px + 26, py + 13], fill=shade(artifact_rgb, 0.7), outline=shade(artifact_rgb, 0.3))
        label = owner_display(artifact)[:7]
        draw.text((px - 2, py + 24), label, fill=(248, 236, 198) if active else (180, 170, 141), font=font_tiny)
        if active:
            draw.rectangle([px - 8, py - 8, px + 42, py + 46], outline=(255, 246, 180), width=3)
            draw.line([px + 17, py - 8, 1202, 176], fill=(255, 226, 132), width=2)

    detail_x = 1160
    draw.rectangle([detail_x, 140, width - 52, 906], fill=(27, 24, 19), outline=(150, 112, 58), width=3)
    draw.rectangle([detail_x + 20, 166, width - 74, 420], fill=(36, 32, 25), outline=(96, 76, 48), width=2)
    draw.text((detail_x + 36, 184), "SELECTED RELIC", fill=(255, 221, 136), font=font_hall)
    draw.text((detail_x + 36, 220), selected["title"][:38], fill=(244, 233, 202), font=font_body)
    draw.text((detail_x + 36, 250), owner_display(selected), fill=(205, 190, 150), font=font_body)
    draw.text((detail_x + 36, 286), selected["hall"], fill=(238, 201, 117), font=font_body)
    draw.text((detail_x + 36, 322), f"Object: {selected['object_guess']}", fill=(228, 218, 188), font=font_body)
    draw.text((detail_x + 36, 352), f"Score: {selected['curation_scores']['curation_score']}  CMD: {selected.get('resource_pack_item', {}).get('custom_model_data', '')}", fill=(228, 218, 188), font=font_body)
    draw.text((detail_x + 36, 382), f"XYZ: {selected['minecraft_coordinates']['x']} {selected['minecraft_coordinates']['y']} {selected['minecraft_coordinates']['z']}", fill=(228, 218, 188), font=font_body)

    plaque = selected["spirit_first_line"][:72]
    draw.rectangle([detail_x + 20, 446, width - 74, 566], fill=(44, 35, 24), outline=(121, 94, 55), width=2)
    draw.text((detail_x + 36, 466), "PLAQUE", fill=(255, 221, 136), font=font_hall)
    draw.text((detail_x + 36, 498), plaque[:40], fill=(240, 226, 190), font=font_body)
    draw.text((detail_x + 36, 528), plaque[40:], fill=(240, 226, 190), font=font_body)

    stats = [
        ("artifact passports", len(collection)),
        ("object families", pack_stats["total_kinds"]),
        ("resource models", pack_stats["total_items"]),
        ("display profiles", pack_stats["total_model_profiles"]),
        ("server import", "ready"),
        ("resource pack", "AfterBlockMuseum.zip"),
    ]
    sy = 604
    for label, value in stats:
        draw.rectangle([detail_x + 24, sy, width - 78, sy + 42], fill=(35, 33, 29), outline=(74, 65, 47))
        draw.text((detail_x + 38, sy + 10), str(label).upper(), fill=(171, 158, 121), font=font_body)
        draw.text((detail_x + 230, sy + 10), str(value)[:24], fill=(246, 225, 164), font=font_body)
        sy += 52

    draw.rectangle([70, 932, width - 70, 986], fill=(27, 24, 19), outline=(88, 70, 46), width=2)
    draw.text((94, 950), "Museum path: upload relic -> classify object -> choose hall -> assign plot -> render item model -> spawn pedestal in Minecraft", fill=(222, 205, 166), font=font_body)

    path = os.path.join(tempfile.gettempdir(), f"afterblock_museum_preview_{selected['artifact_id']}.png")
    image.save(path)
    return path


def catalog_rows(collection: list[dict]) -> list[list]:
    rows = []
    for artifact in collection[:101]:
        rows.append(
            [
                artifact.get("catalog_index", 0),
                owner_display(artifact),
                artifact["title"],
                artifact["object_guess"],
                artifact["hall"],
                artifact["curation_scores"]["curation_score"],
                f"{artifact['minecraft_coordinates']['x']} {artifact['minecraft_coordinates']['y']} {artifact['minecraft_coordinates']['z']}",
                artifact.get("resource_pack_item", {}).get("custom_model_data", ""),
            ]
        )
    return rows


def artifact_wall_html(collection: list[dict]) -> str:
    by_hall = {hall: [] for hall in MUSEUM_HALLS}
    for artifact in collection:
        by_hall.setdefault(artifact["hall"], []).append(artifact)
    selected = collection[0]
    selected_item = selected.get("resource_pack_item", {})
    selected_profile = selected.get("hall_profile") or HALL_PROFILES.get(selected["hall"], {})
    hall_routes = {
        "Hall of Firsts": "Threshold Arcade",
        "Hall of Companions": "Quiet Bench Passage",
        "Hall of Turning Points": "Pressure Door",
        "Hall of Worlds": "Blue Lantern Corridor",
        "Hall of Soft Things": "Shelter Nook",
        "Hall of Tools": "Workshop Walk",
        "Hall of Lost Signals": "Static Archive",
        "Grand Painting Hall": "Frame Gallery",
        "Animal Spirit Grove": "Living Atrium",
    }
    portals = []
    for hall in MUSEUM_HALLS:
        hall_items = by_hall.get(hall, [])
        color = hall_color(hall)
        rgb = f"rgb({color[0]}, {color[1]}, {color[2]})"
        profile = HALL_PROFILES.get(hall, {})
        visible = hall_items[:3]
        relics = []
        for artifact in visible:
            item = artifact.get("resource_pack_item", {})
            active = artifact["artifact_id"] == selected["artifact_id"]
            preview_url = texture_preview_url(item.get("id", "missing")) if item.get("id") else ""
            handle = artifact.get("social_tag") or owner_display(artifact)
            command = f"/give @p minecraft:paper[minecraft:custom_model_data={item.get('custom_model_data', 0)}] 1"
            relics.append(
                f"""
                <details class="portal-relic profile-relic {'active' if active else ''}">
                  <summary>
                    <img src="{html_escape(preview_url)}" alt="{html_escape(artifact['object_guess'])}">
                    <strong>{html_escape(compact_text(artifact['object_guess'].title(), 18))}</strong>
                    <small>Item {html_escape(item.get('custom_model_data', ''))}</small>
                    <span class="social-peek"><b>HF</b>{html_escape(compact_text(handle, 18))}</span>
                  </summary>
                  <div class="profile-popout">
                    <b>{html_escape(artifact['title'])}</b>
                    <p>{html_escape(compact_text(artifact.get('memory_text', artifact.get('plaque_line', '')), 160))}</p>
                    <em>{html_escape(compact_text(artifact.get('spirit_first_line', artifact.get('plaque_line', '')), 120))}</em>
                    <code>{html_escape(command)}</code>
                  </div>
                </details>
                """
            )
        more = max(0, len(hall_items) - len(visible))
        portals.append(
            f"""
            <article class="hall-portal {'active' if hall == selected['hall'] else ''}" style="--hall-color:{rgb}">
              {f"<span class='you-are-here'>You are here</span>" if hall == selected['hall'] else ""}
              <div class="portal-depth">
                <span class="portal-lamp left"></span>
                <span class="portal-lamp right"></span>
                <div class="portal-sign">
                  <strong>{html_escape(hall)}</strong>
                  <em>{html_escape(hall_routes.get(hall, 'Museum Passage'))}</em>
                </div>
              </div>
              <div class="portal-copy">
                <span>{len(hall_items)} relics</span>
                <p>{html_escape(compact_text(profile.get('world', profile.get('when', 'A distinct museum wing.')), 92))}</p>
              </div>
              <div class="portal-relics">{''.join(relics)}{f"<span class='more-chip'>+{more}</span>" if more else ""}</div>
            </article>
            """
        )
    selected_preview = artifact_preview_url(selected)
    selected_command = f"/give @p minecraft:paper[minecraft:custom_model_data={selected_item.get('custom_model_data', 0)}] 1"
    selected_handle = selected.get("social_tag") or owner_display(selected)
    return f"""
    <section class="museum-wall persistent-museum">
      <div class="wall-heading">
        <h3>Living Museum Map</h3>
        <p>The banner follows the selected relic through its hall, plot, item code, and passport route.</p>
      </div>
      <div class="living-map-banner">
        <span>You are here</span>
        <strong>{html_escape(selected['hall'])} · {html_escape(hall_routes.get(selected['hall'], selected['zone']))}</strong>
        <p>{html_escape(selected['title'])} is installed at plot {selected['plot']['x']}, {selected['plot']['z']} with CMD {selected_item.get('custom_model_data', 0)}.</p>
      </div>
      <div class="selected-installation" style="--hall-color:rgb({hall_color(selected['hall'])[0]}, {hall_color(selected['hall'])[1]}, {hall_color(selected['hall'])[2]})">
        <div class="installation-frame">
          <img src="{html_escape(selected_preview)}" alt="{html_escape(selected['object_guess'])}">
          <span>Placed</span>
        </div>
        <div>
          <strong>{html_escape(selected['title'])}</strong>
          <em>{html_escape(selected['hall'])} · {html_escape(hall_routes.get(selected['hall'], selected['zone']))} · XYZ {selected['minecraft_coordinates']['x']} {selected['minecraft_coordinates']['y']} {selected['minecraft_coordinates']['z']}</em>
          <p>{html_escape(compact_text(selected.get('memory_text', selected.get('plaque_line', '')), 150))}</p>
          <code>{html_escape(selected_command)}</code>
          <details class="selected-profile">
            <summary>Open relic profile</summary>
            <div>
              <b>{html_escape(selected.get('spirit_first_line', selected.get('plaque_line', '')))}</b>
              <span>{html_escape(selected.get('lore_short', selected.get('placement_reason', '')))}</span>
            </div>
          </details>
        </div>
        <span class="social-peek selected-social"><b>HF</b>{html_escape(compact_text(selected_handle, 22))}</span>
      </div>
      <div class="museum-concourse">{''.join(portals)}</div>
    </section>
    """


def input_type_from_prompt(prompt: str) -> str:
    text = (prompt or "").lower()
    if any(word in text for word in ["painting", "poster", "mural", "canvas", "draw"]):
        return "painting_prompt"
    if any(word in text for word in ["creature", "pet", "animal", "spirit", "dragon", "bird"]):
        return "animal_spirit"
    if any(word in text for word in ["memory", "childhood", "first", "old", "kept", "carried"]):
        return "memory_prompt"
    return "object_photo"


def build_museum_artifact(
    owner_name: str,
    owner_handle: str,
    input_type: str,
    source_prompt: str,
    memory_text: str,
    relic_image_path: str | None = None,
) -> dict:
    owner_name = (owner_name or "Anonymous").strip()
    owner_handle = social_tag_for(owner_handle)
    input_type = (input_type or "memory_prompt").strip()
    source_prompt = (source_prompt or "a mysterious object from a half-remembered room").strip()
    memory_text = (memory_text or "No memory text was provided, so the museum listens to the object itself.").strip()
    image_note = ""
    image_palette = []
    if relic_image_path:
        try:
            with Image.open(relic_image_path) as uploaded:
                uploaded = uploaded.convert("RGB").resize((8, 8))
                pixels = list(uploaded.getdata())
                avg = tuple(int(sum(pixel[i] for pixel in pixels) / len(pixels)) for i in range(3))
                image_note = f"uploaded image average color rgb{avg}"
                image_palette = [avg]
        except Exception:
            image_note = "uploaded image could not be fingerprinted"
    text = f"afterblock={owner_name}|{owner_handle}|{input_type}|{source_prompt}|{memory_text}|{image_note}"
    seed = stable_seed(text)
    vec = embedding(text)
    moods = top_moods(text, vec)
    palette = palette_from_vector(vec, seed, moods)
    palette_names = [name for name, _ in palette]
    object_guess = object_guess_for(input_type, source_prompt, memory_text)
    hall, placement_reason = hall_for_artifact(input_type, object_guess, source_prompt, memory_text, seed)
    hall_profile = HALL_PROFILES.get(hall, {})
    zone = museum_zone_for(hall, seed)
    plot = plot_for_seed(seed)
    title = artifact_title(source_prompt, seed, moods, object_guess)
    artifact_id = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
    scores = curation_scores(source_prompt, memory_text, input_type, moods, palette_names, plot)
    spirit = spirit_for_artifact(title, object_guess, memory_text, hall, seed)
    coordinates = {"x": plot["world_x"], "y": 80, "z": plot["world_z"]}
    plaque_line = spirit["spirit_first_line"]
    lore_short = f"{object_guess.title()} placed in {hall.lower()} because {placement_reason}."
    resource_item = resource_pack_item_for(object_guess, seed)
    artifact = {
        "artifact_id": artifact_id,
        "owner_name": owner_name,
        "owner_handle": owner_handle,
        "owner_label": owner_handle or owner_name or "anonymous visitor",
        "social_tag": owner_handle,
        "input_type": input_type,
        "title": title,
        "source_prompt": source_prompt,
        "memory_text": memory_text,
        "image_fingerprint": image_note,
        "object_guess": object_guess,
        "hall": hall,
        "hall_profile": hall_profile,
        "zone": zone,
        "plot": plot,
        "minecraft_coordinates": coordinates,
        "palette": palette_names,
        "minecraft_materials": palette_names,
        "texture_path": f"assets/afterblock_textures/items/{texture_key_for(object_guess)}_selected.png",
        "resource_pack_item": resource_item,
        "plaque_line": plaque_line,
        "lore_short": lore_short,
        "artifact_when": hall_profile.get("when", placement_reason),
        "spirit_name": spirit["spirit_name"],
        "spirit_traits": spirit["spirit_traits"],
        "spirit_first_line": spirit["spirit_first_line"],
        "placement_reason": placement_reason,
        "curation_scores": scores,
        "resonance_links": resonance_links_for_artifact(hall, moods, plot),
        "passport_card": {
            "title": title,
            "owner_handle": owner_handle,
            "owner_label": owner_handle or owner_name or "anonymous visitor",
            "hall": hall,
            "plot": plot,
            "minecraft_coordinates": coordinates,
            "plaque_line": plaque_line,
            "preservation_line": "Preserved in AfterBlock Museum",
        },
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    artifact.update(spirit)
    artifact["share_url"] = artifact_share_url(artifact)
    artifact["qr_payload"] = artifact["share_url"]
    return artifact


def museum_packet_for(artifact: dict) -> dict:
    return {
        "type": "dreamwall.museum.v1",
        "artifact": artifact,
        "museum": {
            "hall": artifact["hall"],
            "zone": artifact["zone"],
            "plot": artifact["plot"],
            "coordinates": artifact["minecraft_coordinates"],
            "placement_reason": artifact["placement_reason"],
        },
        "spirit": {
            "name": artifact["spirit_name"],
            "traits": artifact["spirit_traits"],
            "first_line": artifact["spirit_first_line"],
            "rules": artifact["rules"],
            "sample_visitor_questions": artifact["sample_visitor_questions"],
            "sample_spirit_responses": artifact["sample_spirit_responses"],
        },
        "passport": artifact["passport_card"],
        "minecraft": {
            "protocol": "dreamwall.mc.v1",
            "import_mode": "museum_artifact",
            "title": artifact["title"],
            "hall": artifact["hall"],
            "coordinates": artifact["minecraft_coordinates"],
            "materials": artifact["minecraft_materials"],
            "texture_path": artifact["texture_path"],
            "resource_pack_item": artifact["resource_pack_item"],
            "recommended_item": artifact["resource_pack_item"].get("recommended_item", "minecraft:paper"),
            "custom_model_data": artifact["resource_pack_item"].get("custom_model_data", 0),
            "model": artifact["resource_pack_item"].get("model", ""),
            "plaque_text": artifact["plaque_line"],
            "spirit_first_line": artifact["spirit_first_line"],
            "owner_handle": artifact["owner_handle"],
            "owner_label": artifact.get("owner_label", owner_display(artifact)),
            "social_tag": artifact.get("social_tag", ""),
            "artifact_when": artifact.get("artifact_when", ""),
            "passport_qr_payload": artifact["qr_payload"],
            "sign_lines": [
                compact_text(artifact["title"], 30),
                compact_text(artifact.get("owner_label", owner_display(artifact)), 30),
                compact_text(artifact["hall"], 30),
                compact_text(artifact["spirit_first_line"], 30),
            ],
            "pedestal": "place engraved nameplate, 3D resource-pack item, lectern passport book, and redstone profile button at coordinates",
        },
    }


def curate_afterblock_artifact(
    owner_name: str,
    owner_handle: str,
    input_type: str,
    source_prompt: str,
    memory_text: str,
    relic_image_path: str | None = None,
):
    artifact = build_museum_artifact(owner_name, owner_handle, input_type, source_prompt, memory_text, relic_image_path)
    packet = museum_packet_for(artifact)
    collection = museum_collection(artifact, 100)
    preview_path = render_museum_preview(artifact, collection)
    model_view = artifact_model_html(artifact)
    hall_profile = artifact.get("hall_profile") or HALL_PROFILES.get(artifact["hall"], {})
    placement = [
        f"# {artifact['title']}",
        f"**{owner_display(artifact)}** · {artifact['hall']} · score {artifact['curation_scores']['curation_score']}",
        f"Plot **({artifact['plot']['x']}, {artifact['plot']['z']})** · XYZ **{artifact['minecraft_coordinates']['x']} {artifact['minecraft_coordinates']['y']} {artifact['minecraft_coordinates']['z']}**",
        "",
        f"**When it becomes art:** {hall_profile.get('when', artifact['placement_reason'])}",
        f"**Worldbuilding:** {hall_profile.get('world', 'placed as a quiet museum relic')}",
        f"**Minecraft placement:** {hall_profile.get('minecraft', 'pedestal, sign, and item frame')}",
        "",
        f"{artifact['placement_reason']}",
        f"_{artifact['plaque_line']}_",
        "",
        "**Resonance links**",
    ]
    if artifact["resonance_links"]:
        placement.extend(
            f"- {link['title']} by {link['creator']}: {link['resonance']}, distance {link['distance']}"
            for link in artifact["resonance_links"]
        )
    else:
        placement.append("- No nearby resonance yet. This artifact becomes an anchor for future visitors.")
    profile = relic_profile_html(artifact)
    passport = passport_html(artifact)
    command = minecraft_give_command(artifact)
    coordinates = coordinates_html(artifact)
    waypoint = waypointcraft_html(artifact)
    server_kit = server_kit_text(artifact)
    server_handoff = server_handoff_html(artifact)
    return (
        preview_path,
        catalog_rows(collection),
        artifact_wall_html(collection),
        model_view,
        command,
        coordinates,
        waypoint,
        "\n".join(placement),
        profile,
        passport,
        json.dumps(packet, indent=2),
        server_kit,
        server_handoff,
    )


def quick_curate_afterblock_artifact(
    source_prompt: str,
    memory_text: str,
    owner_name: str,
    owner_handle: str,
    relic_image_path: str | None = None,
):
    source_prompt = (source_prompt or "").strip() or "a water bottle beside a laptop monitor"
    input_type = input_type_from_prompt(source_prompt)
    memory_text = (memory_text or "").strip() or (
        "A compact story caption visitors see when they hover the relic in the museum."
    )
    outputs = curate_afterblock_artifact(owner_name, owner_handle, input_type, source_prompt, memory_text, relic_image_path)
    return (*outputs, input_type, source_prompt, memory_text)


def place_in_museum(source_prompt: str, story_caption: str, owner_handle: str = "@Wildstash", relic_image_path: str | None = None):
    owner_name, owner_tag = visitor_identity(owner_handle)
    preview, catalog, wall, model, command, coordinates, waypoint, placement, spirit, passport, packet, server_kit, server_handoff, *_ = quick_curate_afterblock_artifact(
        source_prompt,
        story_caption,
        owner_name,
        owner_tag,
        relic_image_path,
    )
    server_download = server_config_zip(
        import_prompt=clean_text(source_prompt, DEFAULT_IMPORT_PROMPT),
        import_story=clean_text(story_caption, DEFAULT_IMPORT_STORY),
        import_owner=clean_text(owner_handle, DEFAULT_IMPORT_OWNER),
    )
    return model, command, coordinates, waypoint, passport, packet, preview, catalog, spirit, wall, server_kit, server_download, server_handoff


def load_demo_artifact(name: str):
    data = DEMO_ARTIFACTS.get(name) or next(iter(DEMO_ARTIFACTS.values()))
    return (
        data["owner_name"],
        data["owner_handle"],
        data["input_type"],
        data["source_prompt"],
        data["memory_text"],
    )


HABITATS = {
    "redstone caves": ["electric", "mechanical", "small", "curious"],
    "sky forest": ["flying", "social", "light", "watchful"],
    "mushroom swamp": ["fungal", "patient", "camouflaged", "soft"],
    "desert ruins": ["ancient", "defensive", "forager", "heatproof"],
    "ocean cliffs": ["aquatic", "agile", "echoing", "storm"],
    "nether garden": ["cursed", "glowing", "bold", "fireproof"],
}

CREATURE_HINTS = {
    "electric": ["spark", "thunder", "yellow", "lightning", "battery"],
    "flying": ["bird", "sky", "wing", "cloud", "feather"],
    "aquatic": ["ocean", "fish", "wave", "rain", "river"],
    "mechanical": ["robot", "gear", "circuit", "redstone", "machine"],
    "ancient": ["dragon", "ruin", "fossil", "temple", "old"],
    "fungal": ["mushroom", "spore", "swamp", "moss", "rot"],
    "cursed": ["ghost", "void", "shadow", "haunted", "curse"],
    "cozy": ["leaf", "soft", "tiny", "garden", "warm"],
}

SAMPLE_CREATURES = [
    {"name": "Mossbyte", "creator": "feral_dev", "species": "moss circuit fox", "habitat": "redstone caves", "survival": 84, "generation": 3, "state": "foraging near copper lamps"},
    {"name": "Cloudrill", "creator": "sky_bidder", "species": "cloud antler drake", "habitat": "sky forest", "survival": 79, "generation": 2, "state": "guarding a floating nest"},
    {"name": "Funglow", "creator": "anonymous_heron", "species": "glowing swamp moth", "habitat": "mushroom swamp", "survival": 73, "generation": 4, "state": "pollinating red mushrooms"},
    {"name": "Obsidip", "creator": "redacted", "species": "tiny nether seal", "habitat": "nether garden", "survival": 66, "generation": 1, "state": "sleeping under basalt leaves"},
]


def creature_traits(prompt: str, vec: np.ndarray) -> list[str]:
    lowered = prompt.lower()
    traits = []
    for trait, hints in CREATURE_HINTS.items():
        if any(hint in lowered for hint in hints):
            traits.append(trait)
    ranked = sorted(CREATURE_HINTS, key=lambda trait: vec[stable_seed(trait) % len(vec)], reverse=True)
    for trait in ranked:
        if trait not in traits:
            traits.append(trait)
        if len(traits) >= 5:
            break
    return traits[:5]


def habitat_fit(traits: list[str], habitat: str) -> float:
    wanted = HABITATS[habitat]
    return sum(1 for trait in traits if trait in wanted) / max(1, len(wanted))


def hatch_pet(prompt: str, player: str, island: str):
    prompt = (prompt or "").strip() or "a quiet creature made of leaves"
    player = (player or "anonymous").strip()
    island = (island or "founder island").strip()
    text = f"pet={player}\nisland={island}\nprompt={prompt}"
    seed = stable_seed(text)
    vec = embedding(text)
    moods = top_moods(text, vec)
    traits = creature_traits(prompt, vec)
    habitat_names = list(HABITATS)
    habitat = habitat_names[seed % len(habitat_names)]
    fit = habitat_fit(traits, habitat)
    rng = np.random.default_rng(seed)
    stats = {
        "speed": int(3 + abs(vec[1]) * 9),
        "defense": int(3 + abs(vec[7]) * 9),
        "foraging": int(3 + abs(vec[11]) * 9),
        "social": int(3 + abs(vec[17]) * 9),
        "mutation": int(3 + abs(vec[23]) * 9),
    }
    base_survival = 42 + fit * 28 + stats["foraging"] * 1.7 + stats["defense"] * 1.2 + stats["social"] * 0.9
    survival = int(max(12, min(96, base_survival + rng.normal(0, 5))))
    name_parts = ["Volt", "Moss", "Cloud", "Fang", "Bloom", "Rune", "Pip", "Ash", "Glim", "Root"]
    suffixes = ["ling", "paw", "drake", "moth", "sprite", "cub", "wisp", "beak", "tail", "byte"]
    name = name_parts[seed % len(name_parts)] + suffixes[(seed // 9) % len(suffixes)]
    species = f"{traits[0]} {traits[1]} creature" if len(traits) > 1 else f"{traits[0]} creature"
    generation = 1 + seed % 4
    state_options = [
        "searching for food",
        "watching a stronger creature from tall grass",
        "marking a new nest site",
        "training near a redstone gate",
        "avoiding a predator trail",
        "looking for a fusion partner",
    ]
    state = state_options[(seed // 17) % len(state_options)]
    cooldown = 45 + seed % 75
    battle_score = int(stats["speed"] * 1.1 + stats["defense"] * 1.4 + stats["foraging"] * 0.8 + fit * 18)
    lineage = [
        f"Gen 0: {player}'s prompt seed",
        f"Gen {generation}: {name} adapted to {habitat}",
        f"Next possible fusion: {traits[0]} + {moods[0]} lineage",
    ]
    pet = {
        "protocol": "neuropets.mc.v1",
        "name": name,
        "creator": player,
        "species": species,
        "prompt": prompt,
        "island": island,
        "habitat": habitat,
        "traits": traits,
        "moods": moods,
        "stats": stats,
        "survival": survival,
        "battle_score": battle_score,
        "generation": generation,
        "state": state,
        "cooldown_seconds": cooldown,
        "lineage": lineage,
        "spawn": {
            "minecraft_entity": "fox" if "cozy" in traits or "electric" in traits else "allay",
            "name_tag": f"{name} of {player}",
            "particle": "electric_spark" if "electric" in traits else "happy_villager",
            "habitat_marker": habitat,
        },
    }
    return pet


def render_pet_portrait(pet: dict) -> Image.Image:
    seed = stable_seed(json.dumps(pet, sort_keys=True))
    vec = embedding(" ".join(pet["traits"]) + pet["habitat"])
    palette = palette_from_vector(vec, seed, pet["moods"])
    grid = generate_grid(vec, seed, palette)
    image = render_grid(grid, palette)
    draw = ImageDraw.Draw(image)
    draw.rectangle([8, 8, image.width - 8, 42], fill=(24, 18, 12))
    draw.text((16, 17), pet["name"], fill=(245, 225, 169))
    return image


def pet_leaderboard(current: dict) -> str:
    rows = SAMPLE_CREATURES + [
        {
            "name": current["name"],
            "creator": current["creator"],
            "species": current["species"],
            "habitat": current["habitat"],
            "survival": current["survival"],
            "generation": current["generation"],
            "state": current["state"],
        }
    ]
    rows = sorted(rows, key=lambda row: (row["survival"], row["generation"]), reverse=True)
    lines = ["# Survival Leaderboard", ""]
    for i, row in enumerate(rows, 1):
        lines.append(
            f"{i}. **{row['name']}** by {row['creator']} - {row['survival']}% survival, "
            f"Gen {row['generation']}, {row['habitat']} - {row['state']}"
        )
    return "\n".join(lines)


def hatch_neuropet(prompt: str, player: str, island: str):
    pet = hatch_pet(prompt, player, island)
    card = [
        f"# {pet['name']}",
        f"Creator: **{pet['creator']}**",
        f"Species: **{pet['species']}**",
        f"Habitat: **{pet['habitat']}**",
        f"Current state: **{pet['state']}**",
        f"Survival odds: **{pet['survival']}%**",
        f"Battle score: **{pet['battle_score']}**",
        f"Cooldown before another hatch: **{pet['cooldown_seconds']}s**",
        "",
        "Traits: " + ", ".join(pet["traits"]),
        "",
        "Prompt abuse rule: power words become personality/aura, not uncapped strength.",
    ]
    lineage = "\n".join(f"- {item}" for item in pet["lineage"])
    return (
        render_pet_portrait(pet),
        "\n".join(card),
        pet_leaderboard(pet),
        lineage,
        json.dumps(pet, indent=2),
    )


def mutate_grid(grid: np.ndarray, frame_index: int, seed: int, vec: np.ndarray) -> np.ndarray:
    shifted = np.roll(grid, shift=(frame_index % 4) - 1, axis=1)
    shifted = np.roll(shifted, shift=((frame_index * 2) % 5) - 2, axis=0)
    rng = np.random.default_rng(seed + frame_index * 97)
    mask = rng.random(grid.shape) < (0.035 + abs(vec[frame_index % len(vec)]) * 0.04)
    mutated = shifted.copy()
    mutated[mask] = (mutated[mask] + 1 + frame_index) % max(1, int(grid.max()) + 1)
    if frame_index % 3 == 0:
        band = (frame_index * 3) % GRID
        mutated[band : min(GRID, band + 2), :] = np.fliplr(mutated[band : min(GRID, band + 2), :])
    return mutated


def render_graffiti_gif(frames: list[Image.Image], seed: int) -> str:
    path = os.path.join(tempfile.gettempdir(), f"dreamwall_graffiti_{seed}.gif")
    frames[0].save(
        path,
        save_all=True,
        append_images=frames[1:],
        duration=140,
        loop=0,
        optimize=False,
    )
    return path


def keywords_for_title(prompt: str) -> list[str]:
    stop = {
        "the",
        "and",
        "with",
        "from",
        "that",
        "this",
        "into",
        "through",
        "around",
        "made",
        "your",
        "their",
        "over",
        "under",
        "for",
        "a",
        "an",
        "of",
        "in",
        "on",
    }
    words = [word.strip(".,!?;:()[]{}\"'").lower() for word in prompt.split()]
    words = [word for word in words if len(word) >= 4 and word not in stop]
    ranked = sorted(set(words), key=lambda word: (-len(word), word))
    return ranked[:3] or ["wall", "dream"]


def artifact_title(prompt: str, seed: int, moods: list[str], object_guess: str | None = None) -> str:
    normalized_guess = (object_guess or "").strip().lower()
    prompt_text = (prompt or "").lower()
    object_titles = {
        "book": "Book",
        "earbuds": "AirPods" if "airpod" in prompt_text else "Earbuds",
        "monitor": "Monitor",
        "school bag": "School Bag",
        "phone": "Phone",
        "water bottle": "Water Bottle",
        "plush toy": "Teddy Bear" if "teddy" in prompt_text or "bear" in prompt_text else "Plush Toy",
        "sticker": "OpenAI Sticker" if "openai" in prompt_text else "Sticker",
        "shoes": "Shoe" if "shoe" in prompt_text and "shoes" not in prompt_text else "Shoes",
        "painting": "Painting",
        "tool": "Tool",
    }
    if normalized_guess in object_titles:
        return object_titles[normalized_guess]
    keys = keywords_for_title(prompt)
    prefix_bank = {
        "cozy": ["Lantern", "Hearth", "Soft"],
        "cursed": ["Cursed", "Void", "Haunt"],
        "ancient": ["Relic", "Fossil", "Temple"],
        "mechanical": ["Circuit", "Signal", "Chrome"],
        "wild": ["Storm", "Root", "Cloud"],
        "royal": ["Crown", "Banner", "Gold"],
    }
    prefix_options = prefix_bank.get(moods[0], ["Living", "Dream", "Wall"])
    prefix = prefix_options[seed % len(prefix_options)]
    core = " ".join(word.capitalize() for word in keys[:2])
    return f"{prefix} {core}"


def growth_stages(value: float, mutation_rate: float) -> list[dict]:
    max_stage = 1
    if value >= 45:
        max_stage = 2
    if value >= 58:
        max_stage = 3
    if value >= 70:
        max_stage = 4
    if value >= 82 or mutation_rate >= 0.44:
        max_stage = 5
    labels = [
        ("seed sketch", "appears as a small 16x16 study tile"),
        ("wall tile", "claims a full 32x32 block slot"),
        ("animated mural", "loops all 10 frames on the wall"),
        ("fusion landmark", "can merge with nearby artifacts"),
        ("server myth", "earns a named sign and center-wall placement"),
    ]
    return [
        {"stage": idx + 1, "name": name, "unlocked": idx < max_stage, "meaning": meaning}
        for idx, (name, meaning) in enumerate(labels)
    ]


def living_graffiti(prompt: str, player: str, wall_zone: str):
    prompt = (prompt or "").strip() or "a glowing bird made of storm clouds"
    player = (player or "anonymous").strip()
    wall_zone = (wall_zone or "main wall").strip()
    text = f"graffiti={player}\nzone={wall_zone}\nprompt={prompt}"
    seed = stable_seed(text)
    vec = embedding(text)
    moods = top_moods(text, vec)
    palette = palette_from_vector(vec, seed, moods)
    base_grid = generate_grid(vec, seed, palette)
    frames = [render_grid(mutate_grid(base_grid, idx, seed, vec), palette) for idx in range(10)]
    gif_path = render_graffiti_gif(frames, seed)
    palette_names = [name for name, _ in palette]
    plot = plot_for_seed(seed)
    canvas_text, value_packet = canvas_report(prompt, player, moods, palette_names, plot)
    value_data = json.loads(value_packet)
    title = artifact_title(prompt, seed, moods)
    mutation_rate = round(0.18 + abs(vec[5]) * 0.42, 3)
    permanence = int(40 + value_data["valuation"]["creative_value"] * 0.7)
    stages = growth_stages(value_data["valuation"]["creative_value"], mutation_rate)
    unlocked = [stage for stage in stages if stage["unlocked"]]
    next_locked = next((stage for stage in stages if not stage["unlocked"]), None)
    footprint = {
        "blocks": "32 x 32",
        "frames": 10,
        "minecraft_area": "1,024 blocks per frame",
        "wall_slot": f"({plot['x']}, {plot['z']})",
        "world_origin": f"{plot['world_x']} 80 {plot['world_z']}",
        "fallback": "first frame can be placed as static map art if animation is not wired yet",
    }
    storyboard = [
        f"# {title}",
        f"Creator: **{player}**",
        f"Size: **32x32 blocks**, **10 frames**, **1,024 blocks per frame**",
        f"Wall slot: **({plot['x']}, {plot['z']})** in {wall_zone}",
        f"Minecraft origin: **{plot['world_x']} 80 {plot['world_z']}**",
        f"Mutation rate: **{mutation_rate}**",
        f"Creative value: **{value_data['valuation']['creative_value']} demo points**",
        f"Wall permanence: **{permanence}%**",
        f"Growth stage: **{unlocked[-1]['stage']} - {unlocked[-1]['name']}**",
        "",
        "10-frame loop:",
        "1. seed image appears",
        "2. palette drifts",
        "3. motion band crosses the tile",
        "4. nearby context mutates the pattern",
        "5. artifact stabilizes as a named wall memory",
        "",
        "Growth path:",
    ]
    storyboard.extend(
        f"- {'unlocked' if stage['unlocked'] else 'locked'} Stage {stage['stage']}: {stage['name']} - {stage['meaning']}"
        for stage in stages
    )
    if next_locked:
        storyboard.extend(
            [
                "",
                f"Next growth target: raise value/mutation to unlock **Stage {next_locked['stage']} - {next_locked['name']}**.",
            ]
        )
    storyboard.extend(
        [
            "",
            "Why people use it: they can get their name and idea onto a public Minecraft wall that mutates and fuses with other prompts.",
        ]
    )
    packet = {
        "protocol": "living_graffiti.mc.v1",
        "title": title,
        "creator": player,
        "prompt": prompt,
        "wall_zone": wall_zone,
        "plot": plot,
        "frames": 10,
        "footprint": footprint,
        "palette": palette_names,
        "moods": moods,
        "mutation_rate": mutation_rate,
        "permanence": permanence,
        "growth_stages": stages,
        "market": value_data,
        "minecraft": {
            "placement": "animated_wall_tile",
            "fallback": "use first frame as static map art if animation is unavailable",
            "block_size": {"width": 32, "height": 32, "frames": 10},
            "world_origin": f"{plot['world_x']} 80 {plot['world_z']}",
            "wall_label": f"{title} by {player}",
        },
        "trace": {
            "model": MODEL_ID,
            "codex_track_note": "Codex built the Space, packet contract, and demo scaffold.",
        },
    }
    return (
        gif_path,
        "\n".join(storyboard),
        canvas_text,
        json.dumps(packet, indent=2),
    )


def prompt_rows(prompt_block: str) -> list[str]:
    rows = [row.strip() for row in (prompt_block or "").splitlines()]
    return [row for row in rows if row][:18] or LIVING_WALL_PROMPTS


def attention_weather(value: float, mutation_rate: float, neighbors: int) -> str:
    if value >= 78 and neighbors >= 2:
        return "myth storm"
    if mutation_rate >= 0.43:
        return "mutation wind"
    if neighbors >= 2:
        return "fusion bloom"
    if value < 45:
        return "quiet ruins"
    return "steady glow"


def summarize_wall_tile(prompt: str, index: int, wall_zone: str, tick: int) -> dict:
    player = f"builder_{index + 1:02d}"
    text = f"living-wall={wall_zone}\ntick={tick}\nplayer={player}\nprompt={prompt}"
    stable_text = f"living-wall={wall_zone}\nplayer={player}\nprompt={prompt}"
    seed = stable_seed(text)
    stable_tile_seed = stable_seed(stable_text)
    vec = embedding(text)
    moods = top_moods(text, vec)
    palette = palette_from_vector(vec, seed, moods)
    palette_names = [name for name, _ in palette]
    plot = plot_for_seed(stable_tile_seed + index * 31)
    value = valuation(prompt, moods, palette_names, plot)
    mutation_rate = round(0.18 + abs(vec[(tick + index) % len(vec)]) * 0.42, 3)
    stages = growth_stages(value["creative_value"], mutation_rate)
    stage = [item for item in stages if item["unlocked"]][-1]
    neighbors = nearby_artworks(plot)
    return {
        "title": artifact_title(prompt, seed, moods),
        "prompt": prompt,
        "creator": player,
        "plot": plot,
        "minecraft_origin": {
            "x": plot["world_x"],
            "y": 80,
            "z": plot["world_z"],
        },
        "minecraft_bounds": {
            "x1": plot["world_x"],
            "y1": 80,
            "z1": plot["world_z"],
            "x2": plot["world_x"] + PLOT_SCALE - 1,
            "y2": 80 + PLOT_SCALE - 1,
            "z2": plot["world_z"],
        },
        "moods": moods,
        "palette": palette_names,
        "value": value["creative_value"],
        "mutation_rate": mutation_rate,
        "stage": stage,
        "neighbors": neighbors,
        "weather": attention_weather(value["creative_value"], mutation_rate, len(neighbors)),
    }


def tile_distance(left: dict, right: dict) -> int:
    return abs(left["plot"]["x"] - right["plot"]["x"]) + abs(left["plot"]["z"] - right["plot"]["z"])


def fusion_links(tiles: list[dict]) -> list[dict]:
    links = []
    for left_idx, left in enumerate(tiles):
        for right_idx, right in enumerate(tiles[left_idx + 1 :], left_idx + 1):
            distance = tile_distance(left, right)
            shared_moods = sorted(set(left["moods"]).intersection(right["moods"]))
            if distance <= 2 or shared_moods:
                strength = round(max(0.1, (3 - min(distance, 3)) / 3) + len(shared_moods) * 0.18, 2)
                links.append(
                    {
                        "from": left["title"],
                        "to": right["title"],
                        "from_index": left_idx,
                        "to_index": right_idx,
                        "distance": distance,
                        "shared_moods": shared_moods,
                        "strength": strength,
                        "fusion_name": artifact_title(
                            f"{left['prompt']} {right['prompt']}",
                            stable_seed(left["title"] + right["title"]),
                            (shared_moods or left["moods"] or right["moods"])[:2],
                        ),
                    }
                )
    return sorted(links, key=lambda item: (-item["strength"], item["distance"]))[:12]


def evolution_events(tiles: list[dict], links: list[dict], tick: int) -> list[str]:
    events = []
    for tile in sorted(tiles, key=lambda item: (-item["stage"]["stage"], -item["value"]))[:4]:
        events.append(
            f"tick {tick}: {tile['title']} holds Stage {tile['stage']['stage']} "
            f"({tile['stage']['name']}) under {tile['weather']}."
        )
    for link in links[:4]:
        events.append(
            f"tick {tick}: {link['from']} and {link['to']} create fusion pressure "
            f"toward {link['fusion_name']}."
        )
    return events


def render_living_wall_frame(tiles: list[dict], links: list[dict], tick: int, frame: int) -> Image.Image:
    tile_px = 72
    pad = 16
    legend_h = 88
    width = CANVAS_SIZE * tile_px + pad * 2
    height = CANVAS_SIZE * tile_px + pad * 2 + legend_h
    image = Image.new("RGB", (width, height), (25, 24, 22))
    draw = ImageDraw.Draw(image)
    draw.rectangle([0, 0, width, height], fill=(33, 30, 25))
    for x in range(CANVAS_SIZE + 1):
        xx = pad + x * tile_px
        draw.line([xx, pad, xx, pad + CANVAS_SIZE * tile_px], fill=(67, 57, 45), width=1)
    for z in range(CANVAS_SIZE + 1):
        yy = pad + z * tile_px
        draw.line([pad, yy, pad + CANVAS_SIZE * tile_px, yy], fill=(67, 57, 45), width=1)

    for link in links:
        left = tiles[link["from_index"]]
        right = tiles[link["to_index"]]
        x0 = pad + left["plot"]["x"] * tile_px + tile_px // 2
        y0 = pad + left["plot"]["z"] * tile_px + tile_px // 2
        x1 = pad + right["plot"]["x"] * tile_px + tile_px // 2
        y1 = pad + right["plot"]["z"] * tile_px + tile_px // 2
        pulse = int((math.sin((tick + frame) * 0.9 + link["strength"]) + 1) * 35)
        draw.line([x0, y0, x1, y1], fill=(140 + pulse, 216, 174), width=max(1, int(link["strength"] * 3)))

    weather_colors = {
        "myth storm": (240, 204, 86),
        "mutation wind": (180, 94, 210),
        "fusion bloom": (86, 196, 143),
        "quiet ruins": (112, 112, 118),
        "steady glow": (104, 168, 220),
    }
    for tile in tiles:
        x0 = pad + tile["plot"]["x"] * tile_px + 5
        y0 = pad + tile["plot"]["z"] * tile_px + 5
        x1 = x0 + tile_px - 10
        y1 = y0 + tile_px - 10
        color = weather_colors[tile["weather"]]
        pulse = int((math.sin((tick + frame + tile["mutation_rate"] * 10) * 0.8) + 1) * 18)
        fill = tuple(min(255, channel + pulse) for channel in color)
        draw.rectangle([x0, y0, x1, y1], fill=fill, outline=(246, 235, 196), width=2)
        if tile["weather"] in {"mutation wind", "myth storm"}:
            offset = 7 + (frame * 5 + int(tile["mutation_rate"] * 10)) % 34
            draw.line([x0 + offset, y0 + 4, x0 + 4, y0 + offset], fill=(255, 245, 180), width=2)
        if tile["stage"]["stage"] >= 4:
            draw.rectangle([x0 - 3, y0 - 3, x1 + 3, y1 + 3], outline=(255, 216, 92), width=2)
        draw.text((x0 + 6, y0 + 6), tile["title"][:10], fill=(22, 20, 18))
        draw.text((x0 + 6, y1 - 18), f"S{tile['stage']['stage']} V{int(tile['value'])}", fill=(22, 20, 18))

    y = pad + CANVAS_SIZE * tile_px + 22
    draw.text((pad, y), f"Living Canvas tick {tick}.{frame}: prompts claim space, mutate, fuse, and grow into server myths.", fill=(244, 235, 214))
    draw.text((pad, y + 28), "Weather: myth storm / mutation wind / fusion bloom / quiet ruins / steady glow", fill=(205, 190, 160))
    return image


def render_living_wall_animation(tiles: list[dict], links: list[dict], tick: int) -> str:
    frames = [render_living_wall_frame(tiles, links, tick, frame) for frame in range(8)]
    digest = stable_seed(json.dumps([(tile["title"], tile["plot"], tile["weather"]) for tile in tiles], sort_keys=True))
    path = os.path.join(tempfile.gettempdir(), f"dreamwall_living_canvas_{digest}_{tick}.gif")
    frames[0].save(
        path,
        save_all=True,
        append_images=frames[1:],
        duration=180,
        loop=0,
        optimize=False,
    )
    return path


def living_wall_canvas(prompt_block: str, wall_zone: str, tick: int):
    wall_zone = (wall_zone or "main wall").strip()
    prompts = prompt_rows(prompt_block)
    tick = int(tick or 0)
    tiles = [summarize_wall_tile(prompt, idx, wall_zone, tick) for idx, prompt in enumerate(prompts)]
    links = fusion_links(tiles)
    events = evolution_events(tiles, links, tick)
    image = render_living_wall_animation(tiles, links, tick)
    ranked = sorted(tiles, key=lambda item: (item["stage"]["stage"], item["value"], item["mutation_rate"]), reverse=True)
    story = [
        "# Living Moving Canvas",
        "Every prompt claims a coordinate. Nearby ideas fuse. The wall changes weather.",
        "",
        "Evolution events:",
    ]
    story.extend(f"- {event}" for event in events)
    story.extend(
        [
            "",
            "Current strongest artifacts:",
        ]
    )
    for tile in ranked[:5]:
        story.append(
            f"- **{tile['title']}** at ({tile['plot']['x']}, {tile['plot']['z']}): "
            f"Stage {tile['stage']['stage']} {tile['stage']['name']}, {tile['weather']}, "
            f"value {tile['value']}, mutation {tile['mutation_rate']}"
        )
    packet = {
        "protocol": "living_canvas.mc.v1",
        "wall_zone": wall_zone,
        "tick": tick,
        "tile_size_blocks": {"width": 32, "height": 32},
        "canvas_size_tiles": {"width": CANVAS_SIZE, "height": CANVAS_SIZE},
        "minecraft_wall_size_blocks": {
            "width": CANVAS_SIZE * PLOT_SCALE,
            "height": CANVAS_SIZE * PLOT_SCALE,
        },
        "mechanics": [
            "prompt_to_tile",
            "neighbor_fusion",
            "attention_weather",
            "growth_stage_unlocks",
            "server_packet_export",
        ],
        "minecraft_animation_plan": {
            "v1": "place stable 32x32 tiles as map art or wool blocks",
            "v2": "pulse fusion links with particles between tile centers",
            "v3": "periodically update tile frames from the GIF timeline",
            "redstone_required": False,
        },
        "fusion_links": links,
        "evolution_events": events,
        "tiles": tiles,
    }
    return image, "\n".join(story), json.dumps(packet, indent=2)


def server_packet_json(
    prompt: str,
    player: str,
    gallery_zone: str,
    origin: str,
    seed: int,
    moods: list[str],
    palette_names: list[str],
    grid: np.ndarray,
    commands: str,
    plot: dict,
    value_packet: str,
) -> str:
    value_data = json.loads(value_packet)
    packet = {
        "protocol": "dreamwall.mc.v1",
        "job_id": hashlib.sha256(f"{seed}:{prompt}:{player}:{gallery_zone}".encode("utf-8")).hexdigest()[:16],
        "status": "approved_for_demo",
        "player": player,
        "prompt": prompt,
        "gallery_zone": gallery_zone,
        "origin": origin,
        "moods": moods,
        "palette": palette_names,
        "plot": plot,
        "market": value_data,
        "grid": {
            "width": GRID,
            "height": GRID,
            "row_runs": row_runs(grid, [(name, color) for name, color in palette_from_names(palette_names)]),
        },
        "minecraft": {
            "placement": "wall_mosaic",
            "axis": "east_facing",
            "worldedit_preview": commands.splitlines()[:40],
        },
        "trace": {
            "model": MODEL_ID,
            "small_model_constraint": "local semantic fingerprint engine; no cloud model API",
            "identity_rule": "prompt + player + gallery zone jointly shape the wall artifact",
        },
    }
    return json.dumps(packet, indent=2)


def palette_from_names(names: list[str]) -> list[tuple[str, tuple[int, int, int]]]:
    lookup = dict(BLOCKS)
    return [(name, lookup[name]) for name in names if name in lookup]


def make_art(prompt: str, player: str, origin: str, gallery_zone: str) -> ArtResult:
    prompt = (prompt or "").strip()
    player = (player or "anonymous").strip()
    origin = (origin or "~ ~ ~").strip()
    gallery_zone = (gallery_zone or "first wall").strip()
    text = f"player={player}\nzone={gallery_zone}\nprompt={prompt}"
    seed = stable_seed(text)
    vec = embedding(text)
    moods = top_moods(text, vec)
    palette = palette_from_vector(vec, seed, moods)
    grid = generate_grid(vec, seed, palette)
    image = render_grid(grid, palette)
    palette_names = [name for name, _ in palette]
    plot = plot_for_seed(seed)
    if origin == "~ ~ ~":
        origin = f"{plot['world_x']} 80 {plot['world_z']}"
    canvas_text, value_packet = canvas_report(prompt, player, moods, palette_names, plot)

    profile = {
        "artist": player,
        "gallery_zone": gallery_zone,
        "semantic_moods": moods,
        "signature_seed": str(seed),
        "palette": palette_names,
        "tiny_change_rule": "Every character changes the embedding seed; player and wall zone change the final painting.",
    }
    report = (
        f"DreamWall read this as a {', '.join(moods)} artifact for {player}.\n\n"
        f"Palette: {', '.join(palette_names)}.\n\n"
        "Demo beat: type a prompt, generate the painting, then show the same prompt under another player name "
        "to prove the wall remembers identity."
    )
    trace = json.dumps(
        {
            "model": MODEL_ID,
            "parameter_count": "local semantic fingerprint engine, far below 32B",
            "prompt": prompt,
            "player": player,
            "gallery_zone": gallery_zone,
            "moods": moods,
            "palette": palette_names,
        },
        indent=2,
    )
    commands = compact_commands(grid, palette, origin)
    server_packet = server_packet_json(
        prompt=prompt,
        player=player,
        gallery_zone=gallery_zone,
        origin=origin,
        seed=seed,
        moods=moods,
        palette_names=palette_names,
        grid=grid,
        commands=commands,
        plot=plot,
        value_packet=value_packet,
    )
    return ArtResult(image, profile, palette_names, commands, report, trace, server_packet, canvas_text, value_packet)


def gradio_generate(prompt: str, player: str, origin: str, gallery_zone: str):
    result = make_art(prompt, player, origin, gallery_zone)
    return (
        result.image,
        result.report,
        result.commands,
        result.trace,
        json.dumps(result.profile, indent=2),
        result.server_packet,
        result.canvas_report,
        result.valuation_packet,
    )


CSS = """
:root {
  --mc-ink: #f4ecd8;
  --mc-paper: #171410;
  --mc-green: #57744a;
  --mc-gold: #d39b45;
  --museum-stone: #1f211f;
  --museum-panel: #2b251c;
  --museum-glow: #f2c15f;
}
body, .gradio-container {
  background: #10110f !important;
  color: var(--mc-ink);
}
.gradio-container {
  max-width: none !important;
  width: 100% !important;
  padding: 10px 22px 32px !important;
}
.dreamwall-hero {
  position: relative;
  overflow: hidden;
  background:
    linear-gradient(90deg, rgba(14,15,13,0.96) 0%, rgba(24,20,14,0.88) 48%, rgba(12,13,11,0.96) 100%),
    repeating-linear-gradient(90deg, rgba(242,193,95,0.06) 0 1px, transparent 1px 72px);
  border: 2px solid #8b6a3d;
  box-shadow: 0 6px 0 #060605, inset 0 0 36px rgba(242, 193, 95, 0.13);
  padding: 14px 18px;
  margin: 6px 0 10px;
}
.dreamwall-hero h1 {
  margin: 0;
  font-size: 30px;
  color: #ffe4a3;
}
.dreamwall-hero p {
  max-width: 920px;
  font-size: 14px;
  line-height: 1.38;
  margin: 6px 0;
  color: #ead7b0;
}
.badge-row span {
  display: inline-block;
  border: 2px solid #8b6a3d;
  background: #211a12;
  color: #ffdc8a;
  padding: 6px 10px;
  margin: 4px 5px 0 0;
  font-weight: 700;
}
.museum-terminal {
  background: #171916;
  border: 2px solid #6f6a57;
  box-shadow: inset 0 0 18px rgba(242, 193, 95, 0.1);
  padding: 10px 14px;
  margin: 10px 0;
  color: #d8c9a6;
  font-size: 13px;
}
.museum-kiosk {
  background: #181713;
  border: 1px solid #75623d;
  box-shadow: 0 8px 0 #060605, inset 0 0 22px rgba(242, 193, 95, 0.08);
  padding: 14px;
  margin-bottom: 14px;
}
.main-museum-layout {
  align-items: stretch;
  min-height: 0;
}
.prompt-panel {
  min-height: 100%;
}
.prompt-panel .styler,
.prompt-panel .block,
.prompt-panel .form,
.prompt-panel .html-container,
.prompt-panel .prose,
.prompt-panel .wrap,
.prompt-panel .input-container {
  background: transparent !important;
  color: var(--mc-ink) !important;
}
.prompt-panel .block {
  border-color: #4f432b !important;
  box-shadow: none !important;
}
.prompt-panel h2,
.resource-hero h2 {
  margin: 0 0 10px;
  color: #ffe4a3;
}
.prompt-panel label,
.prompt-panel label span {
  color: #d8c9a6 !important;
}
.prompt-panel label.float {
  background: #181713 !important;
  border: 1px solid #5c4d32 !important;
}
.prompt-panel label.container {
  background: #141410 !important;
  border: 1px solid #5c4d32 !important;
}
.prompt-panel textarea {
  min-height: 76px !important;
}
.prompt-panel .image-container,
.prompt-panel .upload-container {
  background: #211d16 !important;
  border-color: #5c4d32 !important;
  color: #e8dcc1 !important;
}
.prompt-panel .upload-container button {
  background: transparent !important;
  color: #e8dcc1 !important;
}
.prompt-panel .source-selection {
  background: #141410 !important;
  border-top: 1px solid #5c4d32 !important;
}
.resource-hero {
  background: #171613;
  border: 1px solid #5c4d32;
  padding: 16px 18px;
  margin: 0 0 12px;
}
.resource-hero p {
  margin: 0;
  max-width: 760px;
  color: #d6c6a4 !important;
}
.resource-controls,
.resource-controls .form,
.resource-controls .wrap,
.resource-controls .block {
  background: transparent !important;
  color: #e8dcc1 !important;
}
.resource-controls label,
.resource-controls label span {
  color: #d8c9a6 !important;
}
.resource-controls input,
.resource-controls button,
.resource-controls .wrap {
  border-color: #5c4d32 !important;
}
.resource-gallery,
.resource-gallery .wrap,
.resource-gallery .gallery,
.resource-gallery .grid-wrap,
.resource-gallery .thumbnail,
.resource-gallery .thumbnail-item {
  background: #15140f !important;
  border-color: #4f432b !important;
}
.resource-gallery img {
  background: radial-gradient(circle at 50% 42%, #3a3021, #11100d 70%) !important;
  border: 1px solid #5c4d32 !important;
  object-fit: contain !important;
}
.resource-gallery .caption-label,
.resource-gallery .caption,
.resource-gallery label {
  color: #ffe4a3 !important;
  background: rgba(20, 16, 10, .86) !important;
}
.museum-kiosk .form {
  border: 0 !important;
}
.museum-kiosk textarea, .museum-kiosk input {
  background: #f4e8cc !important;
  color: #201913 !important;
  border: 2px solid #b88b49 !important;
  font-size: 15px !important;
}
.museum-kiosk button.primary, .museum-kiosk .primary {
  min-height: 46px;
  font-weight: 800 !important;
}
.relic-server-handoff {
  display: grid;
  gap: 8px;
  background:
    linear-gradient(90deg, rgba(232,197,111,.16), rgba(69,110,92,.12)),
    #14130f;
  border: 1px solid #8b6a3d;
  box-shadow: inset 0 0 22px rgba(242,193,95,.08);
  padding: 10px;
  margin: 8px 0 0;
}
.relic-server-handoff span {
  display: inline-block;
  width: max-content;
  color: #1b1308;
  background: #ffdc8a;
  border: 1px solid #fff0bd;
  padding: 3px 7px;
  font-size: 10px;
  font-weight: 1000;
  text-transform: uppercase;
  letter-spacing: .06em;
}
.relic-server-handoff strong {
  display: block;
  color: #ffe4a3;
  font-size: 15px;
  line-height: 1.15;
  margin-top: 6px;
}
.relic-server-handoff p {
  margin: 4px 0 0;
  color: #d8c9a6 !important;
  font-size: 12px;
  line-height: 1.35;
}
.handoff-proof {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 8px;
}
.handoff-proof b {
  min-width: 0;
  color: #20160c !important;
  background: #ead7a6 !important;
  border: 1px solid #9d7c46;
  padding: 6px 7px;
  font-size: 11px;
  overflow-wrap: anywhere;
}
.photo-drop-compact .image-container,
.photo-drop-compact .upload-container {
  min-height: 92px !important;
  height: 104px !important;
  border-style: dashed !important;
  display: grid !important;
  align-content: center !important;
  background:
    linear-gradient(90deg, rgba(232,197,111,.08), rgba(82,126,148,.08)),
    #211d16 !important;
}
.photo-drop-compact img {
  object-fit: contain !important;
  max-height: 104px !important;
}
.photo-drop-compact button {
  min-height: 92px !important;
  font-size: 13px !important;
  font-weight: 800 !important;
}
.photo-drop-compact .source-selection {
  min-height: 28px !important;
  padding: 3px 0 !important;
}
.museum-stage {
  background: radial-gradient(circle at 50% 0%, rgba(242,193,95,0.12), transparent 44%), #11120f;
  border: 1px solid #4f432b;
  padding: 10px;
}
.museum-wall {
  background: #191812;
  border: 2px solid #7d6335;
  box-shadow: inset 0 0 24px rgba(0,0,0,0.5);
  padding: 14px;
  margin-top: 16px;
}
.persistent-museum {
  min-height: 430px;
}
.wall-heading {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: end;
  border-bottom: 1px solid #5c4d32;
  padding-bottom: 10px;
  margin-bottom: 12px;
}
.wall-heading h3 {
  margin: 0;
  color: #ffe4a3;
  font-size: 22px;
}
.wall-heading p {
  margin: 0;
  max-width: 440px;
  color: #cdbd9b;
  font-size: 12px;
}
.living-map-banner {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 8px 12px;
  align-items: center;
  background:
    linear-gradient(90deg, rgba(232,197,111,.16), rgba(86,128,96,.13), rgba(57,90,128,.13)),
    #14130f;
  border: 1px solid #8b6a3d;
  box-shadow: inset 0 0 26px rgba(242,193,95,.08);
  padding: 10px 12px;
  margin-bottom: 12px;
}
.living-map-banner span,
.you-are-here {
  color: #1a1308;
  background: #ffdc8a;
  border: 1px solid #fff0bd;
  box-shadow: 0 2px 0 #070604;
  padding: 4px 8px;
  font-size: 10px;
  font-weight: 1000;
  text-transform: uppercase;
  letter-spacing: .08em;
}
.living-map-banner strong {
  color: #ffe4a3;
  font-size: 16px;
}
.living-map-banner p {
  grid-column: 2;
  margin: -2px 0 0;
  color: #d8c9a6 !important;
  font-size: 12px;
}
.selected-installation {
  position: relative;
  display: grid;
  grid-template-columns: 126px 1fr;
  gap: 16px;
  align-items: center;
  background:
    radial-gradient(circle at 12% 18%, color-mix(in srgb, var(--hall-color) 40%, transparent), transparent 34%),
    linear-gradient(90deg, color-mix(in srgb, var(--hall-color) 24%, #171410), #15120e);
  border: 1px solid color-mix(in srgb, var(--hall-color) 78%, #171410);
  padding: 14px;
  margin-bottom: 14px;
  min-height: 132px;
  box-shadow: inset 0 -18px 28px rgba(0,0,0,.18);
}
.installation-frame {
  position: relative;
  min-height: 104px;
  display: grid;
  place-items: center;
  background:
    linear-gradient(180deg, rgba(255,224,154,.12), transparent),
    #211b13;
  border: 1px solid #6f5832;
  box-shadow: inset 0 0 26px rgba(0,0,0,.32);
}
.installation-frame img {
  width: 96px;
  height: 96px;
  object-fit: contain;
  filter: drop-shadow(0 18px 16px rgba(0,0,0,.42));
}
.installation-frame span {
  position: absolute;
  left: 8px;
  bottom: 7px;
  color: #1b1308;
  background: #e8c56f;
  padding: 2px 6px;
  font-size: 10px;
  font-weight: 900;
}
.selected-installation strong,
.selected-installation em,
.selected-installation code {
  display: block;
}
.selected-installation strong {
  color: #ffe8ad;
  font-size: 22px;
  line-height: 1.1;
}
.selected-installation em {
  color: #d8c9a6;
  font-style: normal;
  font-size: 12px;
  margin-top: 4px;
}
.selected-installation p {
  color: #f1dfb8 !important;
  margin: 8px 0 0;
  font-size: 13px;
}
.selected-installation code {
  width: max-content;
  max-width: 100%;
  color: #20160c !important;
  background: #e8c56f !important;
  white-space: normal;
  word-break: break-word;
  margin-top: 8px;
  padding: 5px 7px;
  font-size: 10px;
}
.museum-concourse {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}
.hall-portal {
  position: relative;
  min-height: 246px;
  overflow: hidden;
  background:
    linear-gradient(180deg, color-mix(in srgb, var(--hall-color) 14%, #302417), #11100d 76%),
    #16130f;
  border: 1px solid color-mix(in srgb, var(--hall-color) 60%, #171410);
  padding: 10px;
  box-shadow: inset 0 -28px 42px rgba(0,0,0,.3);
  transition: transform 180ms ease, border-color 180ms ease, box-shadow 180ms ease;
}
.you-are-here {
  position: absolute;
  z-index: 4;
  top: 8px;
  left: 8px;
}
.hall-portal:hover,
.hall-portal.active {
  transform: translateY(-4px);
  border-color: #ffe4a3;
  box-shadow: 0 9px 0 #070604, 0 0 24px color-mix(in srgb, var(--hall-color) 38%, transparent);
}
.portal-depth {
  position: relative;
  height: 116px;
  background:
    linear-gradient(90deg, rgba(0,0,0,.55), transparent 28%, transparent 72%, rgba(0,0,0,.55)),
    radial-gradient(circle at 50% 100%, color-mix(in srgb, var(--hall-color) 38%, transparent), transparent 45%),
    repeating-linear-gradient(90deg, rgba(255,255,255,.05) 0 1px, transparent 1px 28px),
    #17130e;
  border: 1px solid color-mix(in srgb, var(--hall-color) 38%, #3b2c1a);
  clip-path: polygon(7% 0, 93% 0, 100% 100%, 0 100%);
}
.portal-depth::before {
  content: "";
  position: absolute;
  left: 50%;
  bottom: 0;
  width: 46%;
  height: 86%;
  transform: translateX(-50%);
  background: linear-gradient(180deg, color-mix(in srgb, var(--hall-color) 32%, #050403), #050403);
  border: 8px solid color-mix(in srgb, var(--hall-color) 55%, #6e5229);
  border-bottom: 0;
  border-radius: 90px 90px 0 0;
  box-shadow: inset 0 0 30px rgba(0,0,0,.7);
}
.portal-sign {
  position: absolute;
  left: 18px;
  right: 18px;
  top: 14px;
  z-index: 1;
  text-align: center;
  text-shadow: 0 2px 0 #050403;
}
.portal-sign strong,
.portal-sign em {
  display: block;
}
.portal-sign strong {
  color: #ffe4a3;
  font-size: 15px;
  line-height: 1.1;
}
.portal-sign em {
  color: #dfc989;
  font-size: 10px;
  font-style: normal;
  margin-top: 3px;
}
.portal-lamp {
  position: absolute;
  top: 48px;
  z-index: 2;
  width: 12px;
  height: 20px;
  background: #ffca6f;
  box-shadow: 0 0 18px #ffb84a;
  border: 2px solid #3a2612;
}
.portal-lamp.left { left: 18px; }
.portal-lamp.right { right: 18px; }
.portal-copy {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 10px;
  align-items: start;
  margin: 9px 0;
}
.portal-copy span {
  color: #1b1308;
  background: #e8c56f;
  padding: 3px 7px;
  font-size: 10px;
  font-weight: 900;
  white-space: nowrap;
}
.portal-copy p {
  margin: 0;
  color: #d8c9a6 !important;
  font-size: 11px;
  line-height: 1.35;
}
.portal-relics {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
  align-items: stretch;
}
.portal-relic {
  position: relative;
  min-height: 78px;
  display: grid;
  grid-template-rows: 44px auto auto;
  align-items: center;
  justify-items: center;
  background: rgba(15,13,10,.62);
  border: 1px solid rgba(255,228,163,.16);
  padding: 5px;
  transition: transform 160ms ease, border-color 160ms ease, background 160ms ease;
}
.portal-relic > summary {
  list-style: none;
  display: grid;
  grid-template-rows: 44px auto auto;
  align-items: center;
  justify-items: center;
  width: 100%;
  cursor: pointer;
}
.portal-relic > summary::-webkit-details-marker {
  display: none;
}
.portal-relic[open] {
  grid-column: span 3;
  min-height: 164px;
  align-items: start;
}
.portal-relic.active {
  border-color: #ffe4a3;
  background: rgba(255,228,163,.12);
}
.portal-relic:hover {
  transform: translateY(-2px);
  border-color: rgba(255,228,163,.56);
}
.portal-relic img {
  width: 42px;
  height: 42px;
  object-fit: contain;
  filter: drop-shadow(0 8px 8px rgba(0,0,0,.38));
}
.portal-relic strong,
.portal-relic small {
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.portal-relic strong {
  color: #fff0bd;
  font-size: 10px;
}
.portal-relic small {
  color: #a99976;
  font-size: 9px;
}
.social-peek {
  position: absolute;
  right: 6px;
  top: 6px;
  z-index: 5;
  display: inline-flex;
  align-items: center;
  gap: 5px;
  max-width: calc(100% - 12px);
  opacity: 0;
  transform: translateY(-4px);
  pointer-events: none;
  color: #17100a;
  background: #ffe0a3;
  border: 1px solid rgba(255,245,210,.72);
  box-shadow: 0 5px 12px rgba(0,0,0,.34);
  padding: 3px 6px;
  font-size: 10px;
  line-height: 1;
  font-weight: 900;
  transition: opacity 150ms ease, transform 150ms ease;
}
.social-peek b {
  display: inline-grid;
  place-items: center;
  width: 20px;
  height: 20px;
  border-radius: 999px;
  background: #fff5cf;
  color: #1d1309;
  font-size: 9px;
}
.portal-relic:hover .social-peek,
.selected-installation:hover .social-peek {
  opacity: 1;
  transform: translateY(0);
}
.selected-social {
  top: 12px;
  right: 12px;
}
.profile-popout {
  display: none;
  margin-top: 8px;
  padding: 9px;
  width: 100%;
  background: rgba(12,10,7,.8);
  border: 1px solid rgba(255,228,163,.24);
  color: #e9d9b8;
}
.portal-relic[open] .profile-popout {
  display: block;
}
.profile-popout b,
.profile-popout em,
.profile-popout code {
  display: block;
}
.profile-popout b {
  color: #ffe4a3;
  font-size: 12px;
}
.profile-popout p,
.profile-popout em {
  margin: 5px 0 0;
  color: #d8c9a6 !important;
  font-size: 11px;
  line-height: 1.35;
}
.profile-popout em {
  font-style: normal;
  color: #fff0bd !important;
}
.profile-popout code {
  margin-top: 7px;
  padding: 5px;
  color: #1b1308 !important;
  background: #ead7a6 !important;
  white-space: normal;
  word-break: break-word;
  font-size: 10px;
}
.selected-profile {
  margin-top: 9px;
  max-width: 660px;
}
.selected-profile summary {
  cursor: pointer;
  width: max-content;
  color: #1b1308;
  background: #ffdc8a;
  padding: 5px 8px;
  font-size: 11px;
  font-weight: 900;
}
.selected-profile div {
  margin-top: 8px;
  padding: 9px;
  background: rgba(12,10,7,.58);
  border: 1px solid rgba(255,228,163,.24);
}
.selected-profile b,
.selected-profile span {
  display: block;
  color: #f1dfb8;
  font-size: 12px;
  line-height: 1.45;
}
.selected-profile span {
  color: #d8c9a6;
}
.relic-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}
.relic-card {
  position: relative;
  min-height: 156px;
  background:
    linear-gradient(180deg, rgba(255,255,255,0.05), rgba(0,0,0,0.16)),
    #28231a;
  border: 1px solid color-mix(in srgb, var(--hall-color) 72%, #171410);
  padding: 10px;
  transition: transform 160ms ease, border-color 160ms ease, box-shadow 160ms ease;
}
.relic-card:hover, .relic-card.active {
  transform: translateY(-5px);
  border-color: #ffe4a3;
  box-shadow: 0 10px 0 #080705, 0 0 22px color-mix(in srgb, var(--hall-color) 46%, transparent);
}
.relic-object {
  height: 58px;
  display: grid;
  place-items: center;
  perspective: 180px;
}
.relic-object span:first-child {
  width: 52px;
  height: 40px;
  transform: rotateX(58deg) rotateZ(-25deg);
  background: linear-gradient(135deg, var(--hall-color), #f5d27a);
  border: 4px solid #1b160e;
  box-shadow: 14px 12px 0 rgba(0,0,0,0.28);
}
.relic-object span:nth-child(2) {
  position: absolute;
  width: 22px;
  height: 10px;
  margin-top: 42px;
  background: #d5b36b;
  border: 2px solid #1b160e;
}
.relic-object span:nth-child(3) {
  position: absolute;
  width: 76px;
  height: 9px;
  margin-top: 66px;
  background: #44351f;
}
.relic-copy strong, .relic-copy em, .relic-copy small {
  display: block;
}
.relic-copy strong {
  color: #fff0bd;
  font-size: 13px;
  line-height: 1.2;
  overflow-wrap: anywhere;
}
.relic-copy em {
  color: #d8c9a6;
  font-style: normal;
  font-size: 11px;
  margin-top: 4px;
  overflow-wrap: anywhere;
}
.relic-copy small {
  color: #a99976;
  font-size: 10px;
  margin-top: 3px;
  overflow-wrap: anywhere;
}
.relic-card details {
  margin-top: 9px;
  color: #e8dcc1;
  font-size: 11px;
}
.relic-card summary {
  cursor: pointer;
  color: #ffcf75;
  font-weight: 800;
}
.relic-card code {
  display: block;
  white-space: normal;
  word-break: break-word;
  background: #f3e4c3 !important;
  color: #1e170f !important;
  padding: 6px;
  margin-top: 6px;
}
.selected-strip {
  position: relative;
  display: grid;
  grid-template-columns: 58px 1fr;
  gap: 12px;
  align-items: center;
  background: linear-gradient(90deg, color-mix(in srgb, var(--hall-color) 22%, #171410), #171410);
  border: 1px solid color-mix(in srgb, var(--hall-color) 78%, #171410);
  padding: 12px;
  margin-bottom: 12px;
}
.story-caption {
  position: absolute;
  left: 10px;
  right: 10px;
  bottom: 8px;
  z-index: 2;
  display: block;
  opacity: 0;
  transform: translateY(8px);
  pointer-events: none;
  color: #16120c;
  background: linear-gradient(90deg, rgba(255, 200, 85, .92), rgba(98, 165, 255, .84), rgba(255, 134, 180, .88));
  border: 1px solid rgba(255, 245, 210, .6);
  box-shadow: 0 8px 18px rgba(0,0,0,.34);
  padding: 7px 9px;
  font-size: 11px;
  line-height: 1.3;
  font-weight: 800;
  transition: opacity 160ms ease, transform 160ms ease;
  display: flex;
  align-items: center;
  gap: 7px;
}
.story-caption b {
  display: inline-grid;
  place-items: center;
  flex: 0 0 auto;
  width: 24px;
  height: 24px;
  border-radius: 8px;
  background: #fff1bc;
  color: #1d1309;
  box-shadow: 0 2px 0 rgba(0,0,0,.25);
  font-size: 10px;
}
.story-caption span {
  min-width: 0;
}
.selected-caption {
  left: 78px;
  right: 14px;
  bottom: 12px;
}
.selected-installation .selected-caption {
  left: 148px;
}
.artifact-chip:hover .story-caption,
.selected-strip:hover .story-caption {
  opacity: 1;
  transform: translateY(0);
}
.selected-strip strong,
.selected-strip em,
.selected-strip code {
  display: block;
}
.selected-strip strong {
  color: #ffe8ad;
  font-size: 16px;
  line-height: 1.2;
}
.selected-strip em {
  color: #d8c9a6;
  font-style: normal;
  font-size: 12px;
  margin-top: 3px;
}
.selected-strip code {
  color: #20160c !important;
  background: #e8c56f !important;
  white-space: normal;
  word-break: break-word;
  margin-top: 6px;
  padding: 5px 7px;
  font-size: 10px;
}
.hall-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}
.hall-wing {
  min-height: 168px;
  background:
    linear-gradient(180deg, rgba(255,255,255,0.04), rgba(0,0,0,0.16)),
    color-mix(in srgb, var(--hall-color) 13%, #201a12);
  border: 1px solid color-mix(in srgb, var(--hall-color) 58%, #171410);
  padding: 10px;
  box-shadow: inset 0 0 20px rgba(0,0,0,.28);
}
.hall-wing.active {
  border-color: #ffe4a3;
  box-shadow: 0 8px 0 #070604, 0 0 24px color-mix(in srgb, var(--hall-color) 36%, transparent);
}
.hall-wing header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  border-bottom: 1px solid color-mix(in srgb, var(--hall-color) 44%, #46351d);
  padding-bottom: 6px;
}
.hall-wing h4 {
  margin: 0;
  color: #ffe4a3;
  font-size: 13px;
  line-height: 1.2;
}
.hall-wing header span {
  color: #1b1308;
  background: #e8c56f;
  padding: 2px 6px;
  font-size: 10px;
  font-weight: 800;
  white-space: nowrap;
}
.hall-wing p {
  color: #d8c9a6 !important;
  font-size: 11px;
  line-height: 1.35;
  min-height: 42px;
  margin: 8px 0;
}
.artifact-chip-row {
  display: grid;
  gap: 6px;
}
.artifact-chip {
  position: relative;
  display: grid;
  grid-template-columns: 32px 1fr;
  gap: 7px;
  align-items: center;
  min-height: 42px;
  background: rgba(15,13,10,.54);
  border: 1px solid rgba(255,228,163,.12);
  padding: 5px;
  transition: transform 160ms ease, border-color 160ms ease, background 160ms ease;
}
.artifact-chip.active {
  border-color: #ffe4a3;
  background: rgba(255,228,163,.1);
}
.artifact-chip:hover {
  transform: translateY(-2px);
  border-color: rgba(255,228,163,.5);
}
.artifact-chip strong,
.artifact-chip em,
.artifact-chip small {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.artifact-chip strong {
  color: #fff0bd;
  font-size: 11px;
}
.artifact-chip em {
  color: #cdbd9b;
  font-style: normal;
  font-size: 10px;
}
.artifact-chip small {
  color: #a99976;
  font-size: 9px;
}
.mini-cube {
  width: 25px;
  height: 18px;
  display: block;
  transform: rotateX(58deg) rotateZ(-28deg);
  background: linear-gradient(135deg, var(--hall-color), #ffe1a1);
  border: 3px solid #15100a;
  box-shadow: 8px 7px 0 rgba(0,0,0,.3);
}
.mini-cube.selected {
  width: 42px;
  height: 32px;
}
.more-chip {
  display: inline-block;
  width: max-content;
  color: #1b1308;
  background: #cfa861;
  font-weight: 800;
  font-size: 10px;
  padding: 3px 7px;
}
.artifact-model-shell {
  background: #11120f;
  border: 2px solid #7d6335;
  box-shadow: inset 0 0 28px rgba(242,193,95,.08), 0 8px 0 #070604;
  padding: 8px;
  height: 100%;
}
.artifact-model-frame {
  width: 100%;
  height: min(44vh, 460px);
  min-height: 360px;
  border: 0;
  display: block;
  background: #10110f;
}
.command-copy textarea {
  min-height: 46px !important;
  height: 46px !important;
  white-space: nowrap !important;
  overflow-x: auto !important;
  resize: none !important;
}
.command-copy .wrap {
  min-height: 46px !important;
}
.texture-inspector {
  background: #15140f;
  border: 2px solid #7d6335;
  padding: 12px;
  margin: 10px 0;
}
.texture-inspector header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: end;
  border-bottom: 1px solid #5c4d32;
  padding-bottom: 8px;
}
.texture-inspector h3 {
  margin: 0;
  color: #ffe4a3;
}
.texture-inspector p {
  margin: 0;
  max-width: 650px;
  color: #cdbd9b;
  font-size: 12px;
}
.texture-inspector > div {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
  margin-top: 12px;
}
.texture-inspect-card {
  display: grid;
  grid-template-columns: 104px 1fr;
  gap: 10px;
  min-height: 132px;
  background: #242017;
  border: 1px solid #5e523d;
  padding: 9px;
  transition: transform 160ms ease, border-color 160ms ease, box-shadow 160ms ease;
}
.texture-inspect-card:hover {
  transform: translateY(-4px);
  border-color: #ffe4a3;
  box-shadow: 0 8px 0 #080705;
}
.texture-inspect-card img {
  width: 104px;
  height: 104px;
  object-fit: contain;
  background: radial-gradient(circle at 50% 42%, #332d20, #13120f 72%);
  border: 1px solid #3f382a;
}
.texture-inspect-card strong,
.texture-inspect-card span,
.texture-inspect-card code {
  display: block;
  overflow-wrap: anywhere;
}
.texture-inspect-card strong {
  color: #fff0bd;
  font-size: 13px;
}
.texture-inspect-card span {
  color: #cdbd9b;
  font-size: 11px;
  margin-top: 4px;
}
.texture-inspect-card code {
  color: #11100c !important;
  background: #ead7a6 !important;
  margin-top: 7px;
  padding: 5px;
  font-size: 10px;
}
.waypoint-strip {
  display: grid;
  grid-template-columns: repeat(5, minmax(80px, 1fr));
  gap: 8px;
  align-items: stretch;
  background: #171613;
  border: 1px solid #75623d;
  padding: 10px;
  margin-top: 10px;
}
.waypoint-strip div {
  background: #242017;
  border: 1px solid #5c4d32;
  padding: 8px 10px;
}
.waypoint-strip span,
.waypoint-grid span {
  display: block;
  color: #bca982;
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: .06em;
}
.waypoint-strip strong,
.waypoint-grid strong {
  display: block;
  color: #ffe4a3;
  font-size: 18px;
}
.waypoint-strip code,
.waypoint-card code {
  display: block;
  align-self: center;
  background: #ead7a6 !important;
  color: #1b1308 !important;
  padding: 10px;
  overflow-wrap: anywhere;
}
.waypoint-card {
  background: #171613;
  border: 2px solid #75623d;
  box-shadow: 0 8px 0 #070604;
  padding: 16px;
}
.waypoint-card header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  border-bottom: 1px solid #5c4d32;
  margin-bottom: 12px;
}
.waypoint-card h3 {
  margin: 0 0 8px;
  color: #ffe4a3;
  font-size: 24px;
}
.waypoint-card p {
  margin: 0 0 8px;
  color: #cdbd9b !important;
}
.waypoint-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 12px;
}
.waypoint-grid div {
  background: #242017;
  border: 1px solid #5c4d32;
  padding: 12px;
}
.minecraft-campus-view {
  margin: 14px 0;
  background:
    linear-gradient(180deg, rgba(58,82,61,.2), transparent 34%),
    #11100c;
  border: 1px solid #6b5733;
  overflow: hidden;
}
.campus-heading {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 4px 12px;
  align-items: center;
  padding: 12px;
  border-bottom: 1px solid #4e422d;
}
.campus-heading span {
  grid-row: span 2;
  align-self: start;
  color: #161006;
  background: #ffdc8a;
  border: 1px solid #fff0bd;
  padding: 4px 8px;
  font-size: 10px;
  font-weight: 1000;
  text-transform: uppercase;
  letter-spacing: .08em;
}
.campus-heading h4 {
  margin: 0;
  color: #ffe4a3;
  font-size: 18px;
  line-height: 1.15;
}
.campus-heading p {
  margin: 0;
  color: #d8c9a6 !important;
  font-size: 12px;
  line-height: 1.35;
}
.campus-stage {
  position: relative;
  height: 360px;
  overflow: hidden;
  background:
    radial-gradient(circle at 50% 14%, rgba(255,219,132,.14), transparent 30%),
    linear-gradient(180deg, #171309, #080806 68%);
}
.campus-stage::before {
  content: "";
  position: absolute;
  left: 8%;
  right: 8%;
  bottom: 28px;
  height: 62px;
  background: radial-gradient(ellipse, rgba(0,0,0,.72), transparent 68%);
}
.campus-stage-inner {
  position: absolute;
  inset: 18px 0 0;
}
.campus-tile,
.campus-gate,
.campus-entry-beacon,
.campus-relic-pin {
  position: absolute;
  display: grid;
  place-items: center;
}
.campus-tile {
  width: 28px;
  height: 28px;
  transform: rotate(45deg) skew(-10deg, -10deg);
  transform-origin: center;
  background: color-mix(in srgb, var(--hall-color) 24%, #242017);
  border: 1px solid color-mix(in srgb, var(--hall-color) 54%, #66512e);
  box-shadow: 4px 4px 0 rgba(0,0,0,.45), inset -5px -5px 0 rgba(0,0,0,.18);
}
.campus-tile b {
  transform: rotate(-45deg) skew(10deg, 10deg);
  color: rgba(255,241,199,.44);
  font-size: 7px;
  line-height: 1;
}
.campus-tile.entry-proxy {
  border-color: #9ce5ff;
}
.campus-tile.route {
  background: color-mix(in srgb, #e2bc5e 68%, #262014);
  border-color: #ffe4a3;
  box-shadow: 0 0 14px rgba(255,219,132,.38), 4px 4px 0 rgba(0,0,0,.5);
}
.campus-tile.target {
  background: color-mix(in srgb, var(--hall-color) 60%, #ffe4a3);
  border-color: #fff4c8;
  z-index: 8;
  box-shadow: 0 0 24px color-mix(in srgb, var(--hall-color) 70%, transparent), 5px 5px 0 rgba(0,0,0,.48);
}
.campus-gate {
  width: 78px;
  min-height: 54px;
  translate: -24px 0;
  color: #ffe4a3;
  background:
    linear-gradient(90deg, #7b5426 0 12px, transparent 12px calc(100% - 12px), #7b5426 calc(100% - 12px)),
    radial-gradient(ellipse at 50% 100%, color-mix(in srgb, var(--hall-color) 24%, #090806), #050403 68%);
  border: 1px solid color-mix(in srgb, var(--hall-color) 48%, #6b5733);
  box-shadow: 0 10px 0 rgba(0,0,0,.42);
  z-index: 4;
}
.campus-gate b {
  max-width: 68px;
  color: #ffe4a3;
  font-size: 10px;
  line-height: 1.05;
  text-align: center;
}
.campus-entry-beacon {
  width: 54px;
  min-height: 64px;
  translate: -14px -12px;
  color: #101018;
  background:
    linear-gradient(180deg, #b9f2ff, #6aa8ff 68%, #1e4d68);
  border: 2px solid #e8fbff;
  box-shadow: 0 0 24px rgba(135,222,255,.7), 0 12px 0 rgba(0,0,0,.45);
  z-index: 12;
}
.campus-entry-beacon b {
  font-size: 9px;
  line-height: 1.04;
  text-align: center;
}
.campus-relic-pin {
  min-width: 86px;
  max-width: 132px;
  min-height: 36px;
  translate: -28px 0;
  color: #1b1308;
  background: #ffe4a3;
  border: 2px solid #fff4c8;
  box-shadow: 0 10px 0 rgba(0,0,0,.48), 0 0 18px rgba(255,219,132,.4);
  padding: 6px 8px;
  z-index: 14;
}
.campus-relic-pin::after {
  content: "";
  position: absolute;
  left: 30px;
  bottom: -12px;
  width: 10px;
  height: 10px;
  background: #ffe4a3;
  transform: rotate(45deg);
}
.campus-relic-pin b {
  font-size: 11px;
  line-height: 1.08;
  text-align: center;
}
.campus-proof-strip {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
  padding: 10px 12px 12px;
  border-top: 1px solid #4e422d;
}
.campus-proof-strip span {
  min-width: 0;
  color: #ffe4a3;
  background: #242017;
  border: 1px solid #5c4d32;
  padding: 8px;
  font-size: 11px;
  overflow-wrap: anywhere;
}
.living-route-map {
  display: grid;
  grid-template-columns: minmax(180px, .86fr) minmax(280px, 1.35fr);
  gap: 12px;
  align-items: start;
  margin: 14px 0;
}
.route-map-copy {
  min-height: 100%;
  background: linear-gradient(180deg, rgba(255,228,163,.08), #17130e);
  border: 1px solid #5c4d32;
  padding: 12px;
}
.route-map-copy span,
.route-map-proof span,
.route-map-legend span {
  color: #baa985;
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: .05em;
}
.route-map-copy h4 {
  margin: 6px 0;
  color: #ffe4a3;
  font-size: 18px;
  line-height: 1.12;
}
.route-map-copy p {
  margin: 0;
  color: #d8c9a6 !important;
  font-size: 12px;
  line-height: 1.45;
}
.route-map-grid {
  display: grid;
  grid-template-columns: repeat(12, minmax(22px, 1fr));
  gap: 3px;
  background:
    linear-gradient(180deg, rgba(255,228,163,.08), transparent),
    #0f0e0b;
  border: 1px solid #6b5733;
  padding: 8px;
}
.map-cell {
  position: relative;
  aspect-ratio: 1;
  min-width: 0;
  display: grid;
  place-items: center;
  background: color-mix(in srgb, var(--hall-color) 18%, #201b13);
  border: 1px solid color-mix(in srgb, var(--hall-color) 42%, #2a241a);
  box-shadow: inset 0 -5px 0 rgba(0,0,0,.18);
}
.map-cell b {
  color: rgba(255,241,199,.62);
  font-size: 8px;
  line-height: 1;
}
.map-cell.route {
  background: color-mix(in srgb, #d6a642 58%, #201b13);
  border-color: #f5ce78;
  box-shadow: 0 0 10px rgba(245,206,120,.42), inset 0 -5px 0 rgba(0,0,0,.2);
}
.map-cell.entry {
  background: #3b6a88;
  border-color: #9ce5ff;
}
.map-cell.entry::after,
.map-cell.target::after {
  position: absolute;
  inset: 3px;
  display: grid;
  place-items: center;
  color: #120d08;
  background: #ffe4a3;
  font-size: 8px;
  font-weight: 900;
}
.map-cell.entry::after {
  content: "YOU";
}
.map-cell.target {
  background: color-mix(in srgb, var(--hall-color) 62%, #ffe4a3);
  border-color: #fff0bd;
  box-shadow: 0 0 18px color-mix(in srgb, var(--hall-color) 62%, transparent);
}
.map-cell.target::after {
  content: "RELIC";
}
.route-map-proof {
  grid-column: 1 / -1;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
}
.route-map-proof div {
  background: #242017;
  border: 1px solid #5c4d32;
  padding: 9px;
}
.route-map-proof strong {
  display: block;
  margin-top: 3px;
  color: #ffe4a3;
  font-size: 13px;
  line-height: 1.2;
}
.route-map-legend {
  grid-column: 1 / -1;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}
.route-map-legend span {
  display: inline-flex;
  gap: 6px;
  align-items: center;
  color: #d9caa7;
}
.route-map-legend b {
  width: 13px;
  height: 13px;
  display: inline-block;
  border: 1px solid #6b5733;
}
.legend-entry { background: #3b6a88; }
.legend-route { background: #d6a642; }
.legend-target { background: #ffe4a3; }
.server-setup {
  background: #151410;
  border: 2px solid #75623d;
  box-shadow: 0 8px 0 #070604;
  color: #f5ddb0;
  padding: 20px;
}
.server-setup h2 {
  margin: 0 0 8px;
  color: #ffe4a3;
  font-size: 30px;
}
.server-setup p {
  color: #d4c4a0 !important;
}
.server-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  margin: 18px 0;
}
.server-grid article {
  background: #242017;
  border: 1px solid #5c4d32;
  padding: 14px;
  min-height: 166px;
}
.server-grid article span {
  display: inline-grid;
  place-items: center;
  width: 28px;
  height: 28px;
  background: #f2c15f;
  color: #1b1308;
  font-weight: 900;
  margin-bottom: 10px;
}
.server-grid h3 {
  margin: 0 0 8px;
  color: #ffe4a3;
  font-size: 18px;
}
.server-setup code {
  background: #ead7a6 !important;
  color: #1b1308 !important;
  padding: 2px 6px;
  overflow-wrap: anywhere;
}
.server-formula {
  display: grid;
  grid-template-columns: 180px repeat(3, minmax(0, 1fr));
  gap: 8px;
  align-items: center;
  background: #0e0f0d;
  border: 1px solid #5c4d32;
  padding: 12px;
}
.server-note {
  margin: 16px 0 0;
  border-left: 4px solid #f25a0b;
  padding-left: 12px;
}
.server-config-panel {
  margin-top: 18px;
  padding: 16px;
  border: 2px solid #75623d;
  background: #171613;
}
.server-config-heading h3 {
  margin: 0 0 6px;
  color: #ffe4a3;
  font-size: 22px;
}
.server-config-heading p {
  margin: 0 0 12px;
  color: #d4c4a0 !important;
}
.server-config-panel textarea,
.server-config-panel input {
  background: #ead7a6 !important;
  color: #1b1308 !important;
  border: 1px solid #8d6d37 !important;
}
.server-config-panel button {
  background: #f25a0b !important;
  color: #fff8e6 !important;
  border: 0 !important;
  font-weight: 900 !important;
}
.server-owner-card {
  margin: 16px 0;
  border: 2px solid #8d6d37;
  background:
    linear-gradient(135deg, rgba(74, 112, 83, .18), transparent 46%),
    #12130f;
  box-shadow: 0 8px 0 #070604;
  padding: 16px;
  color: #f5ddb0;
}
.server-owner-card header {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 14px;
  align-items: start;
}
.server-owner-columns {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
  align-items: start;
}
.server-owner-card header {
  border-bottom: 1px solid #5c4d32;
  padding-bottom: 12px;
  margin-bottom: 12px;
}
.server-owner-card header span,
.server-owner-grid article span {
  display: block;
  color: #c9a85a;
  font-size: 12px;
  font-weight: 900;
  text-transform: uppercase;
}
.server-owner-card h3,
.server-owner-card h4 {
  margin: 4px 0 8px;
  color: #ffe4a3;
}
.server-owner-card header b {
  background: #f2c15f;
  color: #1b1308;
  padding: 8px 10px;
  font-weight: 900;
}
.server-owner-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 14px;
}
.server-owner-grid article,
.server-owner-columns > div {
  background: #201c14;
  border: 1px solid #5c4d32;
  padding: 12px;
}
.server-owner-card code {
  background: #ead7a6 !important;
  color: #1b1308 !important;
  padding: 2px 6px;
  overflow-wrap: anywhere;
}
.server-owner-card ol {
  margin: 0;
  padding-left: 20px;
}
.server-owner-card li {
  margin: 0 0 8px;
}
.server-owner-card li span {
  display: block;
  margin-top: 4px;
  color: #d4c4a0;
  overflow-wrap: anywhere;
}
.server-owner-command-strip {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
}
.server-owner-note {
  margin: 12px 0 0;
  color: #d4c4a0 !important;
}
.demo-path {
  border: 2px solid #8d6d37;
  background:
    linear-gradient(135deg, rgba(242, 193, 95, .12), transparent 42%),
    #15130f;
  box-shadow: 0 8px 0 #080705;
  padding: 20px;
}
.demo-path header {
  border-bottom: 1px solid #5c4d32;
  margin-bottom: 14px;
  padding-bottom: 12px;
}
.demo-path h2 {
  margin: 0 0 6px;
  color: #ffe4a3;
}
.demo-path p,
.demo-path li {
  color: #e8dcc1 !important;
}
.demo-path-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}
.demo-path article {
  border: 1px solid #5c4d32;
  background: #211d16;
  padding: 14px;
}
.demo-path article span {
  display: block;
  color: #f2c15f;
  font-weight: 900;
  margin-bottom: 8px;
}
.judge-scorecard {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
  margin-top: 14px;
}
.judge-scorecard article {
  border-color: #775c30;
  background:
    linear-gradient(180deg, rgba(242, 193, 95, .12), transparent),
    #191611;
}
.judge-scorecard strong {
  display: block;
  color: #ffe4a3;
  margin-bottom: 6px;
}
.judge-scorecard code {
  background: #ead7a6 !important;
  color: #1b1308 !important;
  padding: 2px 5px;
}
.demo-path ul,
.demo-script {
  margin: 0;
  padding-left: 18px;
}
.demo-script {
  border: 1px solid #6f5832;
  margin-top: 14px;
  padding: 14px 14px 14px 34px;
  background: #171410;
}
.demo-script b {
  color: #f2c15f;
}
.demo-command-strip {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
  margin-top: 14px;
}
.demo-command-strip code,
.demo-proof-note code {
  display: block;
  background: #ead7a6 !important;
  color: #1b1308 !important;
  padding: 8px;
  overflow-wrap: anywhere;
}
.demo-closing-line {
  border-left: 4px solid #f25a0b;
  margin: 14px 0 8px;
  padding-left: 12px;
  font-weight: 900;
}
.demo-proof-note {
  display: grid;
  grid-template-columns: 140px repeat(3, minmax(0, 1fr));
  gap: 8px;
  align-items: center;
  margin: 0;
  color: #cdbd9b !important;
}
.demo-proof-note span {
  color: #f2c15f;
  font-weight: 900;
}
.passport-card {
  background:
    linear-gradient(135deg, rgba(255, 226, 154, .1), transparent 35%),
    #221d16;
  border: 3px solid #b98a46;
  box-shadow: 0 8px 0 #080705, inset 0 0 24px rgba(242, 193, 95, 0.14);
  color: #f9e4b4;
  padding: 20px;
}
.passport-header {
  display: flex;
  justify-content: space-between;
  gap: 18px;
  align-items: flex-start;
  border-bottom: 1px solid #725a34;
  padding-bottom: 14px;
  margin-bottom: 16px;
}
.passport-card h2 {
  margin: 4px 0;
  font-size: clamp(28px, 4vw, 46px);
  line-height: 1.02;
  color: #ffe6a6;
}
.passport-kicker {
  color: #e2b86f;
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}
.passport-owner {
  color: #cdbd9b;
}
.passport-share {
  display: grid;
  grid-template-columns: auto;
  gap: 6px;
  align-items: center;
  justify-items: center;
  color: #cdbd9b;
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: .08em;
}
.passport-share-actions,
.profile-share-actions {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.passport-share-link,
.profile-share,
.passport-share-icon,
.profile-share-icon {
  display: inline-grid;
  place-items: center;
  min-height: 30px;
  padding: 5px 9px;
  color: #1b1308 !important;
  background: #ffe0a3;
  border: 1px solid #fff0bd;
  text-decoration: none !important;
  font-weight: 1000;
  letter-spacing: 0;
  text-transform: none;
  box-shadow: 0 3px 0 #090704;
}
.passport-share-icon,
.profile-share-icon {
  width: 32px;
  padding: 5px;
  font-size: 16px;
}
.hf-icon {
  display: grid;
  place-items: center;
  width: 50px;
  height: 50px;
  border-radius: 14px;
  background: linear-gradient(135deg, #ffcc4d, #ff8f66);
  color: #221409;
  font-weight: 1000;
  box-shadow: 0 5px 0 #090704;
}
.mini-qr {
  display: grid;
  grid-template-columns: repeat(11, 6px);
  gap: 2px;
  padding: 8px;
  background: #f9edcf;
  border: 2px solid #120f0a;
}
.mini-qr span {
  width: 6px;
  height: 6px;
  background: transparent;
}
.mini-qr span.on {
  background: #15100a;
}
.passport-grid {
  display: grid;
  grid-template-columns: minmax(220px, 320px) 1fr;
  gap: 16px;
}
.passport-preview {
  min-height: 210px;
  border: 2px solid #6f6a57;
  background:
    radial-gradient(circle at 50% 34%, rgba(242,193,95,.22), transparent 42%),
    repeating-linear-gradient(45deg, #2b2d29 0, #2b2d29 10px, #242520 10px, #242520 20px);
  display: flex;
  flex-wrap: wrap;
  align-content: center;
  justify-content: center;
  gap: 8px;
  padding: 12px;
}
.passport-artifact-image {
  width: min(100%, 230px);
  height: 180px;
  object-fit: contain;
  background: radial-gradient(circle at 50% 42%, rgba(242,193,95,.18), #13120f 72%);
  border: 1px solid #5c4d32;
  box-shadow: inset 0 0 22px rgba(0,0,0,.32), 0 16px 18px rgba(0,0,0,.22);
}
.passport-preview strong,
.passport-preview em {
  width: 100%;
  display: block;
  text-align: center;
}
.passport-preview strong {
  color: #ffe4a3;
  font-size: 22px;
}
.passport-preview em {
  color: #d4c39d;
  font-style: normal;
}
.passport-object-mark {
  width: 100%;
  text-align: center;
}
.passport-facts p {
  margin: 10px 0;
  color: #e8dcc1 !important;
}
.passport-route {
  display: grid;
  grid-template-columns: 1.2fr 1fr auto;
  gap: 8px;
  align-items: center;
  margin: 10px 0;
  border: 1px solid #6f5832;
  background: #171410;
  padding: 10px;
}
.passport-route strong,
.passport-route span {
  display: block;
  color: #ffe4a3;
}
.passport-route span {
  color: #d8c9a6;
  font-size: 12px;
}
.passport-scan {
  display: grid;
  grid-template-columns: 140px 1fr;
  gap: 14px;
  align-items: center;
  margin-top: 14px;
  border-top: 1px solid #725a34;
  padding-top: 14px;
}
.passport-qr-image {
  width: 140px;
  height: 140px;
  background: #f8edcf;
  border: 3px solid #120f0a;
  image-rendering: pixelated;
}
.passport-scan strong,
.passport-scan span {
  display: block;
}
.passport-scan strong {
  color: #ffe4a3;
  font-size: 18px;
}
.passport-scan p {
  margin: 4px 0 6px;
  color: #e8dcc1 !important;
  font-size: 12px;
  line-height: 1.4;
}
.passport-scan span {
  color: #d8c9a6;
  overflow-wrap: anywhere;
  font-size: 12px;
}
.passport-facts code {
  background: #ead7a6 !important;
  color: #1b1308 !important;
  padding: 5px 7px;
}
.relic-profile-page {
  background:
    radial-gradient(circle at 8% 12%, rgba(242,193,95,.16), transparent 32%),
    #171410;
  border: 2px solid #7d6335;
  box-shadow: 0 8px 0 #080705, inset 0 0 28px rgba(242,193,95,.08);
  padding: 18px;
  color: #f4ecd8;
}
.relic-profile-page header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
  border-bottom: 1px solid #5c4d32;
  padding-bottom: 12px;
  margin-bottom: 14px;
}
.profile-kicker {
  display: block;
  color: #d8b66f;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: .08em;
}
.relic-profile-page h2 {
  margin: 5px 0;
  color: #ffe4a3;
  font-size: clamp(28px, 4vw, 44px);
  line-height: 1.02;
}
.relic-profile-page header p {
  margin: 0;
  color: #d8c9a6 !important;
}
.profile-grid {
  display: grid;
  grid-template-columns: 1.2fr 1fr;
  gap: 12px;
}
.profile-grid article {
  background: #211d16;
  border: 1px solid #5c4d32;
  padding: 14px;
}
.profile-grid h3 {
  margin: 0 0 8px;
  color: #ffe4a3;
}
.profile-grid p {
  margin: 0;
  color: #e8dcc1 !important;
  line-height: 1.55;
}
.profile-lore {
  margin-top: 10px !important;
  color: #ffdc8a !important;
  font-weight: 800;
}
.profile-grid code {
  display: block;
  color: #1b1308 !important;
  background: #ead7a6 !important;
  padding: 8px;
  white-space: normal;
  word-break: break-word;
  margin-bottom: 10px;
}
.coordinate-cards {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
  margin-bottom: 12px;
}
.coordinate-cards span {
  background: #171410;
  border: 1px solid #6f5832;
  padding: 10px;
}
.coordinate-cards small {
  display: block;
  color: #bca982;
  font-size: 10px;
  text-transform: uppercase;
}
.coordinate-cards strong {
  display: block;
  color: #ffe4a3;
  font-size: 20px;
}
.museum-swatch {
  width: 30px;
  height: 30px;
  border: 2px solid #0b0b09;
  display: inline-block;
}
.floor-map {
  display: grid;
  grid-template-columns: repeat(12, 18px);
  gap: 3px;
  margin-top: 12px;
}
.floor-cell {
  width: 18px;
  height: 18px;
  background: #34372f;
  border: 1px solid #57513f;
  color: #1b160e;
  text-align: center;
  line-height: 18px;
  transition: transform 130ms ease, background 130ms ease, box-shadow 130ms ease;
}
.floor-cell.near {
  background: #414432;
}
.floor-cell:hover {
  transform: scale(1.45);
  background: #75a9ff;
  box-shadow: 0 0 12px #75a9ff;
}
.floor-cell.active {
  background: #f2c15f;
  box-shadow: 0 0 10px #f2c15f;
  animation: plotPulse 1.4s ease-in-out infinite;
}
.passport-map-card {
  margin-top: 14px;
  padding: 14px;
  border: 2px solid #75623d;
  background: #171613;
}
.passport-map-card h3 {
  margin: 0;
  color: #ffe4a3;
}
.passport-map-card p {
  margin: 6px 0 0;
  color: #cdbd9b !important;
}
@keyframes plotPulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.24); }
}
textarea, input {
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace !important;
}
.prose, .markdown, .gradio-container p, .gradio-container li {
  color: #e8dcc1 !important;
}
.prose h1, .prose h2, .prose h3, .markdown h1, .markdown h2, .markdown h3,
.prose strong, .markdown strong {
  color: #ffe4a3 !important;
}
.gradio-container code, .gradio-container pre {
  color: #2b2114 !important;
}
.compact-note {
  color: #c9b98f;
  font-size: 13px;
  margin: 0 0 8px;
}
.scan-passport-panel {
  max-width: 980px;
  margin: 0 auto 18px;
  border: 2px solid #7eb6ff;
  background:
    linear-gradient(90deg, rgba(80, 126, 181, .32), transparent 62%),
    #121722;
  box-shadow: 0 8px 0 #05070a, inset 0 0 26px rgba(126, 182, 255, .12);
  color: #edf6ff;
  padding: 16px;
}
.scan-passport-panel[hidden] {
  display: none;
}
.scan-passport-inner {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 16px;
  align-items: start;
}
.scan-passport-inner span {
  display: block;
  color: #9fd0ff;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: .08em;
}
.scan-passport-inner h2 {
  margin: 4px 0 6px;
  color: #f8e6af;
  font-size: clamp(24px, 3vw, 38px);
}
.scan-passport-inner p,
.scan-passport-inner em {
  margin: 0;
  color: #d8e7f7 !important;
  font-style: normal;
}
.scan-passport-route {
  display: grid;
  grid-template-columns: repeat(3, minmax(80px, 1fr));
  gap: 8px;
  margin-top: 12px;
}
.scan-passport-route b,
.scan-passport-inner code {
  display: block;
  border: 1px solid #5f7896;
  background: rgba(4, 8, 13, .58);
  color: #f8e6af !important;
  padding: 8px;
  overflow-wrap: anywhere;
}
.scan-passport-actions {
  display: grid;
  gap: 8px;
  min-width: 120px;
}
.scan-passport-actions button {
  border: 1px solid #9fd0ff;
  background: transparent;
  color: #edf6ff;
  min-height: 32px;
  padding: 6px 10px;
  cursor: pointer;
}
.scan-passport-actions button:first-child {
  background: #9fd0ff;
  color: #07111d;
  font-weight: 900;
}
@media (max-width: 860px) {
  .relic-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .hall-grid {
    grid-template-columns: 1fr;
  }
  .selected-strip {
    grid-template-columns: 42px 1fr;
  }
  .artifact-model-frame {
    height: 340px;
  }
  .wall-heading {
    display: block;
  }
  .server-grid,
  .server-formula,
  .server-owner-card header,
  .server-owner-grid,
  .server-owner-columns,
  .judge-scorecard,
  .demo-path-grid,
  .demo-command-strip,
  .demo-proof-note,
  .campus-proof-strip,
  .route-map-proof {
    grid-template-columns: 1fr;
  }
  .campus-heading {
    grid-template-columns: 1fr;
  }
  .campus-heading span {
    grid-row: auto;
    justify-self: start;
  }
  .campus-stage {
    height: 330px;
    overflow-x: auto;
  }
  .campus-stage-inner {
    width: 560px;
    min-width: 560px;
  }
  .living-route-map {
    grid-template-columns: 1fr;
  }
}
"""

PASSPORT_SCAN_JS = r"""
() => {
  const escapeHtml = (value) => String(value ?? "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;"
  }[char]));
  const decodeToken = (token) => {
    const padded = token + "=".repeat((4 - token.length % 4) % 4);
    const binary = atob(padded.replace(/-/g, "+").replace(/_/g, "/"));
    const bytes = Uint8Array.from(binary, (char) => char.charCodeAt(0));
    return JSON.parse(new TextDecoder().decode(bytes));
  };
  const renderScannedPassport = () => {
    const panel = document.getElementById("afterblock-scan-panel");
    if (!panel) {
      window.setTimeout(renderScannedPassport, 250);
      return;
    }
    const params = new URLSearchParams(window.location.hash.replace(/^#/, ""));
    const token = params.get("passport");
    if (!token) {
      panel.hidden = true;
      panel.innerHTML = "";
      return;
    }
    try {
      const data = decodeToken(token);
      const xyz = data.xyz || {};
      const shareUrl = `${window.location.origin}${window.location.pathname}${window.location.search}#passport=${encodeURIComponent(token)}`;
      panel.hidden = false;
      panel.innerHTML = `
        <div class="scan-passport-inner">
          <div>
            <span>Scanned AfterBlock Passport</span>
            <h2>${escapeHtml(data.title)}</h2>
            <p>${escapeHtml(data.owner)} · ${escapeHtml(data.object)} · ${escapeHtml(data.hall)} / ${escapeHtml(data.zone)}</p>
            <em>${escapeHtml(data.caption)}</em>
            <div class="scan-passport-route">
              <b>XYZ ${escapeHtml(xyz.x)} ${escapeHtml(xyz.y)} ${escapeHtml(xyz.z)}</b>
              <b>CMD ${escapeHtml(data.cmd)}</b>
              <b>${escapeHtml(data.artifact_id)}</b>
            </div>
            <code>${escapeHtml(data.command)}</code>
          </div>
          <div class="scan-passport-actions">
            <button type="button" data-copy-share>Copy link</button>
            <button type="button" data-close-scan aria-label="Close scanned passport">Close</button>
          </div>
        </div>
      `;
      const copyButton = panel.querySelector("[data-copy-share]");
      copyButton?.addEventListener("click", async () => {
        try {
          await navigator.clipboard.writeText(shareUrl);
          copyButton.textContent = "Copied";
        } catch (error) {
          window.prompt("Copy passport link", shareUrl);
        }
      });
      const closeButton = panel.querySelector("[data-close-scan]");
      closeButton?.addEventListener("click", () => {
        history.replaceState(null, "", window.location.pathname + window.location.search);
        panel.hidden = true;
      });
      panel.scrollIntoView({ behavior: "smooth", block: "start" });
    } catch (error) {
      panel.hidden = false;
      panel.textContent = "This passport QR could not be decoded.";
    }
  };
  window.addEventListener("hashchange", renderScannedPassport);
  window.setTimeout(renderScannedPassport, 350);
}
"""

DEFAULT_MUSEUM_PROMPT = DEFAULT_IMPORT_PROMPT
DEFAULT_STORY_CAPTION = DEFAULT_IMPORT_STORY
INITIAL_MUSEUM_OUTPUTS = place_in_museum(DEFAULT_MUSEUM_PROMPT, DEFAULT_STORY_CAPTION, DEFAULT_IMPORT_OWNER, None)
INITIAL_TEXTURE_OUTPUTS = browse_texture_library("all", 1)
INITIAL_SERVER_CONFIG_KIT = server_config_kit_text()
INITIAL_SERVER_CONFIG_ZIP = server_config_zip()
INITIAL_SERVER_OWNER_CARD = server_owner_install_card_html()


with gr.Blocks(css=CSS, js=PASSPORT_SCAN_JS, title="AfterBlock Museum") as demo:
    gr.HTML(
        """
        <section class="dreamwall-hero">
          <h1>AfterBlock Museum</h1>
          <p>
            Type one object, attach the story people should know, then place it as one persistent Minecraft relic.
          </p>
          <div class="badge-row">
            <span>One prompt</span>
            <span>Story caption</span>
            <span>Minecraft item-code resource pack</span>
          </div>
        </section>
        """
    )
    gr.HTML('<section id="afterblock-scan-panel" class="scan-passport-panel" hidden></section>')

    with gr.Tabs():
        with gr.Tab("Place in Museum"):
            with gr.Row(elem_classes=["main-museum-layout"]):
                with gr.Column(scale=4):
                    with gr.Group(elem_classes=["museum-kiosk", "prompt-panel"]):
                        gr.HTML("<h2>Place in the museum</h2>")
                        quick_prompt = gr.Textbox(
                            label="Museum prompt",
                            placeholder="Example: blue school bag from exam week",
                            lines=2,
                            value=DEFAULT_MUSEUM_PROMPT,
                        )
                        quick_spirit = gr.Textbox(
                            label="Story caption",
                            placeholder="What should visitors know when they open this relic?",
                            lines=3,
                            value=DEFAULT_STORY_CAPTION,
                        )
                        quick_handle = gr.Textbox(
                            label="Visitor signature",
                            placeholder="@handle or display name",
                            lines=1,
                            value="@Wildstash",
                        )
                        quick_button = gr.Button("Place in Museum", variant="primary")
                        museum_server_handoff = gr.HTML(
                            value=INITIAL_MUSEUM_OUTPUTS[12],
                            label="Live Paper handoff",
                        )
                        museum_relic_server_download = gr.File(
                            value=INITIAL_MUSEUM_OUTPUTS[11],
                            label="Download Paper server kit for this relic",
                        )
                        museum_command = gr.Textbox(
                            value=INITIAL_MUSEUM_OUTPUTS[1],
                            label="Minecraft command",
                            lines=2,
                            max_lines=2,
                            show_copy_button=True,
                            elem_classes=["command-copy"],
                        )
                        quick_image = gr.Image(
                            label="Optional image reference",
                            type="filepath",
                            sources=["upload", "clipboard"],
                            height=96,
                            elem_classes=["photo-drop-compact"],
                        )
                with gr.Column(scale=6):
                    museum_model = gr.HTML(value=INITIAL_MUSEUM_OUTPUTS[0], label="Artifact model")
                    museum_coordinates = gr.HTML(value=INITIAL_MUSEUM_OUTPUTS[2], label="Coordinates")

            museum_wall = gr.HTML(value=INITIAL_MUSEUM_OUTPUTS[9], label="Persistent museum")

            with gr.Accordion("Blueprint and catalog", open=False):
                with gr.Row():
                    with gr.Column(scale=5):
                        with gr.Group(elem_classes=["museum-stage"]):
                            museum_preview = gr.Image(value=INITIAL_MUSEUM_OUTPUTS[6], label="Museum map", type="filepath", height=420)
                    with gr.Column(scale=5):
                        museum_catalog = gr.Dataframe(
                            value=INITIAL_MUSEUM_OUTPUTS[7],
                            headers=["#", "creator", "title", "object", "hall", "score", "xyz", "cmd"],
                            label="Generated relic catalog",
                            row_count=8,
                            col_count=(8, "fixed"),
                            interactive=False,
                        )

        with gr.Tab("Resource Pack"):
            gr.HTML(
                """
                <section class="resource-hero">
                  <h2>Resource Pack Browser</h2>
                  <p>Inspect the generated Minecraft item textures and item-code commands without crowding the main museum workflow.</p>
                </section>
                """
            )
            with gr.Row(elem_classes=["resource-controls"]):
                texture_kind = gr.Dropdown(label="Kind", choices=texture_kind_choices(), value="all")
                texture_page = gr.Number(label="Shelf", value=1, precision=0)
                texture_button = gr.Button("Browse Shelf")
            texture_status = gr.Markdown(value=INITIAL_TEXTURE_OUTPUTS[3])
            texture_gallery = gr.Gallery(
                value=INITIAL_TEXTURE_OUTPUTS[0],
                label="PNG previews with Minecraft item codes",
                columns=8,
                height=920,
                object_fit="contain",
                elem_classes=["resource-gallery"],
            )
            with gr.Accordion("Model rows and downloads", open=False):
                texture_table = gr.Dataframe(
                    value=INITIAL_TEXTURE_OUTPUTS[1],
                    headers=["cmd", "label", "kind", "shape", "material", "finish", "profile", "orientation", "itemdisplay", "elements", "model", "give command"],
                    label="Minecraft model rows",
                    row_count=14,
                    col_count=(12, "fixed"),
                    interactive=False,
                )
                texture_inspector = gr.HTML(value=INITIAL_TEXTURE_OUTPUTS[2], label="Model/material inspection wall")
                with gr.Row():
                    gr.File(value=RESOURCE_PACK_PATH, label="Download resource pack")
                    gr.File(value="assets/afterblock_textures/afterblock_manifest.json", label="Download manifest")
                    gr.File(value="assets/afterblock_textures/gallery/index.html", label="Download full texture gallery")

        with gr.Tab("Passport"):
            museum_passport = gr.HTML(value=INITIAL_MUSEUM_OUTPUTS[4], label="Passport")

        with gr.Tab("Placement"):
            museum_waypoint = gr.HTML(value=INITIAL_MUSEUM_OUTPUTS[3], label="Placement")

        with gr.Tab("Packet"):
            museum_packet = gr.Textbox(
                value=INITIAL_MUSEUM_OUTPUTS[5],
                label="dreamwall.museum.v1",
                lines=22,
                max_lines=28,
                show_copy_button=True,
            )

        with gr.Tab("Relic Profile"):
            museum_spirit = gr.HTML(value=INITIAL_MUSEUM_OUTPUTS[8])

        with gr.Tab("Demo Path"):
            gr.HTML(value=demo_path_html(), label="Hackathon demo path")

        with gr.Tab("Minecraft Server"):
            gr.HTML(value=server_setup_html(), label="Minecraft server setup")
            with gr.Group(elem_classes=["server-config-panel"]):
                gr.HTML(
                    """
                    <section class="server-config-heading">
                      <h3>Configure your Paper museum</h3>
                      <p>Keep the coordinate contract fixed, then set the Space, pack, world, and default relic that /dreamwall import should place.</p>
                    </section>
                    """
                )
                with gr.Row():
                    server_space_url = gr.Textbox(
                        label="Public Space URL",
                        value=PUBLIC_SPACE_URL,
                        lines=1,
                    )
                    server_gallery_world = gr.Textbox(
                        label="Minecraft world",
                        value="world",
                        lines=1,
                    )
                server_resource_pack_url = gr.Textbox(
                    label="Resource pack URL",
                    value=RESOURCE_PACK_URL,
                    lines=1,
                )
                with gr.Row():
                    server_resource_pack_sha1 = gr.Textbox(
                        label="Resource pack SHA1",
                        value=RESOURCE_PACK_SHA1,
                        lines=1,
                    )
                    server_offer_pack = gr.Checkbox(
                        label="Offer resource pack on join",
                        value=False,
                    )
                server_import_prompt = gr.Textbox(
                    label="Default /dreamwall import prompt",
                    value=DEFAULT_IMPORT_PROMPT,
                    lines=2,
                    placeholder="Example: blue school bag from exam week",
                )
                server_import_story = gr.Textbox(
                    label="Default /dreamwall import story",
                    value=DEFAULT_IMPORT_STORY,
                    lines=3,
                    placeholder="The caption that becomes the passport/history text",
                )
                server_import_owner = gr.Textbox(
                    label="Default visitor signature",
                    value=DEFAULT_IMPORT_OWNER,
                    lines=1,
                    placeholder="@handle or display name",
                )
                server_config_button = gr.Button("Build Server Config")
                server_owner_card = gr.HTML(
                    value=INITIAL_SERVER_OWNER_CARD,
                    label="Server owner install card",
                )
                server_config_kit = gr.Textbox(
                    value=INITIAL_SERVER_CONFIG_KIT,
                    label="plugins/DreamWall/config.yml and first-run commands",
                    lines=24,
                    max_lines=30,
                    show_copy_button=True,
                )
                server_config_download = gr.File(
                    value=INITIAL_SERVER_CONFIG_ZIP,
                    label="Download complete Paper server kit ZIP",
                )
                with gr.Row():
                    gr.File(
                        value=PAPER_PLUGIN_JAR_PATH,
                        label="Download Paper bridge plugin",
                    )
                    gr.File(
                        value=RESOURCE_PACK_PATH,
                        label="Download resource pack",
                    )
                    gr.File(
                        value=PREBUILT_WORLD_PATH,
                        label="Download prebuilt demo world",
                    )
            museum_server_kit = gr.Textbox(
                value=INITIAL_MUSEUM_OUTPUTS[10],
                label="Current relic server kit",
                lines=28,
                max_lines=34,
                show_copy_button=True,
            )

    quick_button.click(
        place_in_museum,
        inputs=[quick_prompt, quick_spirit, quick_handle, quick_image],
        outputs=[
            museum_model,
            museum_command,
            museum_coordinates,
            museum_waypoint,
            museum_passport,
            museum_packet,
            museum_preview,
            museum_catalog,
            museum_spirit,
            museum_wall,
            museum_server_kit,
            museum_relic_server_download,
            museum_server_handoff,
        ],
        api_name="quick_curate",
    )
    server_config_button.click(
        server_config_bundle,
        inputs=[
            server_space_url,
            server_resource_pack_url,
            server_resource_pack_sha1,
            server_gallery_world,
            server_offer_pack,
            server_import_prompt,
            server_import_story,
            server_import_owner,
        ],
        outputs=[server_config_kit, server_config_download, server_owner_card],
        api_name="server_config_kit",
    )
    texture_button.click(
        browse_texture_library,
        inputs=[texture_kind, texture_page],
        outputs=[texture_gallery, texture_table, texture_inspector, texture_status],
        api_name="browse_textures",
    )


if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=int(os.getenv("PORT", "7860")),
    )
