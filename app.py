import hashlib
import json
import math
import os
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone

import gradio as gr
import numpy as np
from PIL import Image, ImageDraw, ImageFont


MODEL_ID = "dreamwall-local-semantic-fingerprint-v1"
GRID = 32
SCALE = 12


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
    anchors = np.abs(vec[: len(BLOCKS)])
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
    if any(word in text for word in ["airpods", "bag", "friend", "carried", "companion"]):
        return "Hall of Companions", "it stayed close to the owner through ordinary days"
    if any(word in text for word in ["exam", "trade", "turning", "changed", "panic"]):
        return "Hall of Turning Points", "the object sits near a decision or pressure point"
    if any(word in text for word in ["star wars", "galaxy", "home", "world", "dragon"]):
        return "Hall of Worlds", "it opened a world larger than the room around it"
    if any(word in text for word in ["soft", "noise", "private", "morning"]):
        return "Hall of Soft Things", "the memory is quiet, protective, and intimate"
    if any(word in text for word in ["monitor", "tool", "screen", "keyboard"]):
        return "Hall of Tools", "the artifact helped the owner act on the world"
    if any(word in text for word in ["signal", "lost", "radio", "noise"]):
        return "Hall of Lost Signals", "the artifact carries private signal through public static"
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
    return f"""
    <section class="passport-card">
      <div class="passport-kicker">Preserved in AfterBlock Museum</div>
      <h2>{artifact['title']}</h2>
      <p class="passport-owner">{artifact['owner_handle']} · {artifact['hall']}</p>
      <div class="passport-grid">
        <div class="passport-preview">{swatches}<strong>{artifact['spirit_name']}</strong></div>
        <div>
          <p><strong>Plot</strong> ({artifact['plot']['x']}, {artifact['plot']['z']})</p>
          <p><strong>Coordinates</strong> {artifact['minecraft_coordinates']['x']} {artifact['minecraft_coordinates']['y']} {artifact['minecraft_coordinates']['z']}</p>
          <p><strong>Plaque</strong> {artifact['plaque_line']}</p>
          <p><strong>QR payload</strong> <code>{artifact['qr_payload']}</code></p>
        </div>
      </div>
    </section>
    """


def floor_map_html(artifact: dict) -> str:
    cells = []
    for z in range(CANVAS_SIZE):
        for x in range(CANVAS_SIZE):
            active = x == artifact["plot"]["x"] and z == artifact["plot"]["z"]
            label = "★" if active else ""
            cells.append(f"<span class='floor-cell {'active' if active else ''}'>{label}</span>")
    return f"<div class='floor-map'>{''.join(cells)}</div>"


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
        "page_count": max(1, math.ceil(len(manifest) / 30)),
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
        <p>{len(items)} visible on page {page_index}/{page_count}; {total} matching relics. Each card maps to a PNG texture, cuboid item model, material finish, pose profile, and CustomModelData.</p>
      </header>
      <div>{''.join(cards)}</div>
    </section>
    """


def browse_texture_library(kind: str, page: int):
    manifest = resource_manifest()
    if kind and kind != "all":
        manifest = [item for item in manifest if item.get("kind") == kind]
    page_size = 30
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
        f" | page {page_index}/{page_count}"
        " | base item: minecraft:paper"
    )
    return gallery, rows, texture_inspection_html(items, total, page_index, page_count), status


def museum_collection(selected: dict, count: int = 100) -> list[dict]:
    artifacts = [demo_collection_artifact(i) for i in range(count)]
    selected_copy = dict(selected)
    selected_copy["catalog_index"] = 0
    selected_copy["texture_path"] = f"assets/afterblock_textures/items/{texture_key_for(selected['object_guess'])}_selected.png"
    selected_copy["resource_pack_item"] = resource_pack_item_for(selected["object_guess"], stable_seed(selected["artifact_id"]))
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
        label = artifact["owner_handle"][:7]
        draw.text((px - 2, py + 24), label, fill=(248, 236, 198) if active else (180, 170, 141), font=font_tiny)
        if active:
            draw.rectangle([px - 8, py - 8, px + 42, py + 46], outline=(255, 246, 180), width=3)
            draw.line([px + 17, py - 8, 1202, 176], fill=(255, 226, 132), width=2)

    detail_x = 1160
    draw.rectangle([detail_x, 140, width - 52, 906], fill=(27, 24, 19), outline=(150, 112, 58), width=3)
    draw.rectangle([detail_x + 20, 166, width - 74, 420], fill=(36, 32, 25), outline=(96, 76, 48), width=2)
    draw.text((detail_x + 36, 184), "SELECTED RELIC", fill=(255, 221, 136), font=font_hall)
    draw.text((detail_x + 36, 220), selected["title"][:38], fill=(244, 233, 202), font=font_body)
    draw.text((detail_x + 36, 250), selected["owner_handle"], fill=(205, 190, 150), font=font_body)
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
                artifact["owner_handle"],
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
    cards = []
    for artifact in collection[:24]:
        item = artifact.get("resource_pack_item", {})
        score = artifact["curation_scores"]["curation_score"]
        active = artifact.get("catalog_index", 1) == 0
        color = hall_color(artifact["hall"])
        rgb = f"rgb({color[0]}, {color[1]}, {color[2]})"
        cards.append(
            f"""
            <article class="relic-card {'active' if active else ''}" style="--hall-color:{rgb}">
              <div class="relic-object">
                <span></span><span></span><span></span>
              </div>
              <div class="relic-copy">
                <strong>{artifact['title'][:34]}</strong>
                <em>{artifact['owner_handle']} · {artifact['object_guess']}</em>
                <small>{artifact['hall']} · score {score} · CMD {item.get('custom_model_data', '')}</small>
              </div>
              <details>
                <summary>Inspect</summary>
                <p>{artifact['plaque_line'][:130]}</p>
                <code>/give @p minecraft:paper[minecraft:custom_model_data={item.get('custom_model_data', 0)}] 1</code>
              </details>
            </article>
            """
        )
    return f"""
    <section class="museum-wall">
      <div class="wall-heading">
        <h3>Walk the AfterBlock wall</h3>
        <p>Hover a relic to lift it. Open Inspect for the plaque, owner, and Minecraft item command.</p>
      </div>
      <div class="relic-grid">{''.join(cards)}</div>
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
    owner_handle = (owner_handle or "@unknown").strip()
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
    zone = museum_zone_for(hall, seed)
    plot = plot_for_seed(seed)
    title = artifact_title(source_prompt, seed, moods)
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
        "input_type": input_type,
        "title": title,
        "source_prompt": source_prompt,
        "memory_text": memory_text,
        "image_fingerprint": image_note,
        "object_guess": object_guess,
        "hall": hall,
        "zone": zone,
        "plot": plot,
        "minecraft_coordinates": coordinates,
        "palette": palette_names,
        "minecraft_materials": palette_names,
        "texture_path": f"assets/afterblock_textures/items/{texture_key_for(object_guess)}_selected.png",
        "resource_pack_item": resource_item,
        "plaque_line": plaque_line,
        "lore_short": lore_short,
        "spirit_name": spirit["spirit_name"],
        "spirit_traits": spirit["spirit_traits"],
        "spirit_first_line": spirit["spirit_first_line"],
        "placement_reason": placement_reason,
        "curation_scores": scores,
        "resonance_links": resonance_links_for_artifact(hall, moods, plot),
        "passport_card": {
            "title": title,
            "owner_handle": owner_handle,
            "hall": hall,
            "plot": plot,
            "minecraft_coordinates": coordinates,
            "plaque_line": plaque_line,
            "preservation_line": "Preserved in AfterBlock Museum",
        },
        "qr_payload": f"afterblock://artifact/{artifact_id}",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    artifact.update(spirit)
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
            "passport_qr_payload": artifact["qr_payload"],
            "pedestal": "place sign, item frame, and blocky preview at coordinates",
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
    placement = [
        f"# {artifact['title']}",
        f"**{artifact['owner_handle']}** · {artifact['hall']} · score {artifact['curation_scores']['curation_score']}",
        f"Plot **({artifact['plot']['x']}, {artifact['plot']['z']})** · XYZ **{artifact['minecraft_coordinates']['x']} {artifact['minecraft_coordinates']['y']} {artifact['minecraft_coordinates']['z']}**",
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
    spirit_lines = [
        f"# {artifact['spirit_name']}",
        f"Traits: {', '.join(artifact['spirit_traits'])}",
        f"First line: _{artifact['spirit_first_line']}_",
        "",
        "Visitor questions and spirit responses:",
    ]
    for question, response in zip(artifact["sample_visitor_questions"], artifact["sample_spirit_responses"]):
        spirit_lines.append(f"- **{question}** {response}")
    passport = passport_html(artifact) + floor_map_html(artifact)
    return (
        preview_path,
        catalog_rows(collection),
        artifact_wall_html(collection),
        "\n".join(placement),
        spirit_lines and "\n".join(spirit_lines),
        passport,
        json.dumps(packet, indent=2),
    )


def quick_curate_afterblock_artifact(
    source_prompt: str,
    owner_name: str,
    owner_handle: str,
    relic_image_path: str | None = None,
):
    source_prompt = (source_prompt or "").strip() or "a water bottle beside a laptop monitor"
    input_type = input_type_from_prompt(source_prompt)
    memory_text = (
        "One-line museum intake. The curator extracts the object, hall, texture profile, and Minecraft placement from the prompt."
    )
    outputs = curate_afterblock_artifact(owner_name, owner_handle, input_type, source_prompt, memory_text, relic_image_path)
    return (*outputs, input_type, source_prompt, memory_text)


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


def artifact_title(prompt: str, seed: int, moods: list[str]) -> str:
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
    core = "".join(word.capitalize() for word in keys[:2])
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
  max-width: 1240px !important;
}
.dreamwall-hero {
  position: relative;
  overflow: hidden;
  background:
    linear-gradient(90deg, rgba(14,15,13,0.96) 0%, rgba(24,20,14,0.88) 48%, rgba(12,13,11,0.96) 100%),
    repeating-linear-gradient(90deg, rgba(242,193,95,0.06) 0 1px, transparent 1px 72px);
  border: 2px solid #8b6a3d;
  box-shadow: 0 10px 0 #060605, inset 0 0 36px rgba(242, 193, 95, 0.13);
  padding: 24px 28px;
  margin: 14px 0 14px;
}
.dreamwall-hero h1 {
  margin: 0;
  font-size: 38px;
  color: #ffe4a3;
}
.dreamwall-hero p {
  max-width: 820px;
  font-size: 17px;
  line-height: 1.45;
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
.passport-card {
  background: #221d16;
  border: 3px solid #b98a46;
  box-shadow: 0 8px 0 #080705, inset 0 0 24px rgba(242, 193, 95, 0.14);
  color: #f9e4b4;
  padding: 18px;
}
.passport-card h2 {
  margin: 4px 0;
  font-size: 30px;
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
.passport-grid {
  display: grid;
  grid-template-columns: minmax(160px, 240px) 1fr;
  gap: 16px;
}
.passport-preview {
  min-height: 150px;
  border: 2px solid #6f6a57;
  background: repeating-linear-gradient(45deg, #2b2d29 0, #2b2d29 10px, #242520 10px, #242520 20px);
  display: flex;
  flex-wrap: wrap;
  align-content: center;
  justify-content: center;
  gap: 8px;
  padding: 12px;
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
}
.floor-cell.active {
  background: #f2c15f;
  box-shadow: 0 0 10px #f2c15f;
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
@media (max-width: 860px) {
  .relic-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .wall-heading {
    display: block;
  }
}
"""


with gr.Blocks(css=CSS, title="DreamWall MC") as demo:
    gr.HTML(
        """
        <section class="dreamwall-hero">
          <h1>DreamWall: AfterBlock Museum</h1>
          <p>
            Type one relic, memory, object, or creature. The museum classifies it, chooses a hall,
            renders a labeled collection, and emits a Minecraft-ready item packet.
          </p>
          <div class="badge-row">
            <span>Adventure in Thousand Token Wood</span>
            <span>OpenAI Codex Track</span>
            <span>Custom UI</span>
            <span>Paper Bridge</span>
          </div>
        </section>
        """
    )
    gr.HTML("<h2>AfterBlock Museum</h2>")
    with gr.Group(elem_classes=["museum-kiosk"]):
        with gr.Row():
            quick_prompt = gr.Textbox(
                label="Museum prompt",
                placeholder="Example: my scratched blue water bottle from school, with a sticker of a moon on it",
                lines=2,
                value="white AirPods from my first year of university",
                scale=7,
            )
            quick_image = gr.Image(label="Optional object photo", type="filepath", height=118, scale=2)
            quick_button = gr.Button("Place in Museum", variant="primary", scale=2)

    with gr.Row():
        with gr.Column(scale=6):
            with gr.Group(elem_classes=["museum-stage"]):
                museum_preview = gr.Image(label="Museum render: 100 labeled artifacts", type="filepath", height=520)
            museum_wall = gr.HTML(label="Interactive artifact wall")
        with gr.Column(scale=4):
            with gr.Tabs():
                with gr.Tab("Placement"):
                    museum_placement = gr.Markdown()
                with gr.Tab("Spirit"):
                    museum_spirit = gr.Markdown()
                with gr.Tab("Passport"):
                    museum_passport = gr.HTML()
                with gr.Tab("Minecraft Packet"):
                    museum_packet = gr.Textbox(label="dreamwall.museum.v1", lines=14, max_lines=24)
            with gr.Accordion("Catalog table", open=False):
                museum_catalog = gr.Dataframe(
                    headers=["#", "handle", "title", "object", "hall", "score", "xyz", "cmd"],
                    label="Artifact catalog",
                    row_count=8,
                    col_count=(8, "fixed"),
                    interactive=False,
                )

    with gr.Accordion("Advanced curator controls", open=False):
        with gr.Row():
            demo_choice = gr.Dropdown(
                label="Seeded demo relic",
                choices=list(DEMO_ARTIFACTS),
                value="AirPods from first year of university",
            )
            owner_name = gr.Textbox(label="Owner name", value="Arnav")
            owner_handle = gr.Textbox(label="Owner handle", value="@Wildstash")
        with gr.Row():
            input_type = gr.Dropdown(
                label="Input type",
                choices=["object_photo", "painting_prompt", "memory_prompt", "animal_spirit"],
                value="object_photo",
            )
            relic_prompt = gr.Textbox(
                label="Scan relic / prompt",
                lines=2,
                value="white AirPods from my first year of university",
            )
            memory_text = gr.Textbox(
                label="Memory text",
                lines=2,
                value="They carried private worlds through public noise during my first year away.",
            )
        relic_image = gr.Image(label="Advanced image override", type="filepath", height=120)
        museum_button = gr.Button("Curate with Advanced Controls", variant="secondary")

    demo_choice.change(
        load_demo_artifact,
        inputs=[demo_choice],
        outputs=[owner_name, owner_handle, input_type, relic_prompt, memory_text],
    )
    quick_button.click(
        quick_curate_afterblock_artifact,
        inputs=[quick_prompt, owner_name, owner_handle, quick_image],
        outputs=[
            museum_preview,
            museum_catalog,
            museum_wall,
            museum_placement,
            museum_spirit,
            museum_passport,
            museum_packet,
            input_type,
            relic_prompt,
            memory_text,
        ],
        api_name="quick_curate",
    )
    museum_button.click(
        curate_afterblock_artifact,
        inputs=[owner_name, owner_handle, input_type, relic_prompt, memory_text, relic_image],
        outputs=[museum_preview, museum_catalog, museum_wall, museum_placement, museum_spirit, museum_passport, museum_packet],
        api_name="curate_artifact",
    )
    demo.load(
        curate_afterblock_artifact,
        inputs=[owner_name, owner_handle, input_type, relic_prompt, memory_text, relic_image],
        outputs=[museum_preview, museum_catalog, museum_wall, museum_placement, museum_spirit, museum_passport, museum_packet],
    )

    with gr.Accordion("Resource Pack Browser", open=False):
        with gr.Row():
            texture_kind = gr.Dropdown(label="Kind", choices=texture_kind_choices(), value="all")
            texture_page = gr.Slider(label="Page", minimum=1, maximum=resource_pack_stats()["page_count"], value=1, step=1)
            texture_button = gr.Button("Browse Textures")
        texture_status = gr.Markdown()
        texture_gallery = gr.Gallery(
            label="PNG previews with CustomModelData",
            columns=5,
            height=360,
            object_fit="contain",
        )
        texture_table = gr.Dataframe(
            headers=["cmd", "label", "kind", "shape", "material", "finish", "profile", "orientation", "itemdisplay", "elements", "model", "give command"],
            label="Minecraft model rows",
            row_count=8,
            col_count=(12, "fixed"),
            interactive=False,
        )
        texture_inspector = gr.HTML(label="Model/material inspection wall")
        with gr.Row():
            gr.File(value="resource-pack/AfterBlockMuseum.zip", label="Download resource pack")
            gr.File(value="assets/afterblock_textures/afterblock_manifest.json", label="Download manifest")
            gr.File(value="assets/afterblock_textures/gallery/index.html", label="Download full texture gallery")
        texture_button.click(
            browse_texture_library,
            inputs=[texture_kind, texture_page],
            outputs=[texture_gallery, texture_table, texture_inspector, texture_status],
            api_name="browse_textures",
        )
        demo.load(
            browse_texture_library,
            inputs=[texture_kind, texture_page],
            outputs=[texture_gallery, texture_table, texture_inspector, texture_status],
        )

    gr.HTML("<h2>Living Wall Tile</h2>")
    with gr.Row():
        with gr.Column(scale=5):
            graffiti_prompt = gr.Textbox(
                label="Artifact prompt",
                lines=3,
                value="a cloud bird carrying a glowing AI sigil through a thunderstorm",
            )
            graffiti_player = gr.Textbox(label="Creator signature", value="ArnavS")
            graffiti_zone = gr.Textbox(label="Wall zone", value="main wall, launch row")
            graffiti_button = gr.Button("Grow Living Wall Artifact", variant="primary")
        with gr.Column(scale=4):
            graffiti_gif = gr.Image(label="10-frame 32x32-block living graffiti loop", type="filepath", height=360)
    with gr.Row():
        graffiti_story = gr.Markdown(label="Artifact story")
        graffiti_canvas = gr.Textbox(label="Fusion/value readout", lines=14, max_lines=20)
    with gr.Tabs():
        with gr.Tab("Minecraft Animated Wall Packet"):
            graffiti_packet = gr.Textbox(label="living_graffiti.mc.v1", lines=20, max_lines=28)

    graffiti_button.click(
        living_graffiti,
        inputs=[graffiti_prompt, graffiti_player, graffiti_zone],
        outputs=[graffiti_gif, graffiti_story, graffiti_canvas, graffiti_packet],
        api_name="living_graffiti",
    )

    gr.HTML("<h2>Living Canvas</h2>")
    with gr.Row():
        with gr.Column(scale=5):
            wall_prompts = gr.Textbox(
                label="People's imagination feed - one prompt per line",
                lines=8,
                value="\n".join(LIVING_WALL_PROMPTS),
            )
            wall_zone = gr.Textbox(label="Shared Minecraft wall zone", value="main wall, public imagination board")
            wall_tick = gr.Slider(label="Evolution tick", minimum=0, maximum=24, value=3, step=1)
            wall_button = gr.Button("Simulate Living Canvas", variant="primary")
        with gr.Column(scale=4):
            wall_image = gr.Image(label="Animated shared 12x12 Minecraft wall map", type="filepath", height=460)
    with gr.Row():
        wall_story = gr.Markdown(label="Canvas behavior")
        wall_packet = gr.Textbox(label="living_canvas.mc.v1", lines=18, max_lines=26)

    wall_button.click(
        living_wall_canvas,
        inputs=[wall_prompts, wall_zone, wall_tick],
        outputs=[wall_image, wall_story, wall_packet],
        api_name="living_canvas",
    )

    gr.HTML("<h2>NeuroPets Hatchery</h2>")
    with gr.Row():
        with gr.Column(scale=5):
            pet_prompt = gr.Textbox(
                label="Creature seed prompt",
                lines=3,
                value="a shy thunder creature that protects redstone caves",
            )
            pet_player = gr.Textbox(label="Creator name", value="ArnavS")
            pet_island = gr.Textbox(label="Island / server zone", value="founder island")
            hatch_button = gr.Button("Hatch NeuroPet", variant="primary")
        with gr.Column(scale=4):
            pet_image = gr.Image(label="Creature portrait", type="pil", height=360)
    with gr.Row():
        pet_card = gr.Markdown(label="Creature card")
        pet_leaders = gr.Markdown(label="Survival leaderboard")
    with gr.Tabs():
        with gr.Tab("Lineage Wall"):
            pet_lineage = gr.Textbox(label="Descendants and ancestry", lines=8, max_lines=12)
        with gr.Tab("Minecraft Creature Packet"):
            pet_packet = gr.Textbox(label="Spawn/simulation packet", lines=18, max_lines=26)

    hatch_button.click(
        hatch_neuropet,
        inputs=[pet_prompt, pet_player, pet_island],
        outputs=[pet_image, pet_card, pet_leaders, pet_lineage, pet_packet],
        api_name="hatch_pet",
    )

    gr.HTML("<h2>DreamWall Canvas</h2>")
    with gr.Row():
        with gr.Column(scale=5):
            prompt = gr.Textbox(
                label="Whisper to the wall",
                lines=4,
                value="a tiny fox wizard guarding a ruined ocean temple",
            )
            player = gr.Textbox(label="Player signature", value="ArnavS")
            gallery_zone = gr.Textbox(label="Gallery zone", value="moss wing, west wall")
            origin = gr.Textbox(label="Minecraft wall origin", value="~ ~ ~")
            button = gr.Button("Carve this into the DreamWall", variant="primary")
        with gr.Column(scale=4):
            art = gr.Image(label="Minecraft painting preview", type="pil", height=420)
    with gr.Row():
        report = gr.Markdown(label="Wall reading")
        profile = gr.Textbox(label="Artist fingerprint", lines=12, max_lines=16)
    with gr.Tabs():
        with gr.Tab("Minecraft Bridge Packet"):
            packet = gr.Textbox(
                label="Plugin-ready JSON packet",
                lines=18,
                max_lines=26,
            )
        with gr.Tab("Canvas Value / Fusion"):
            canvas = gr.Textbox(label="Plot, fusion, and value", lines=18, max_lines=24)
            value_json = gr.Textbox(label="Voting / auction packet", lines=16, max_lines=22)
        with gr.Tab("WorldEdit / Plugin Plan"):
            commands = gr.Textbox(label="Mural instructions", lines=18, max_lines=24)
        with gr.Tab("Open Trace"):
            trace = gr.Textbox(label="Trace for Sharing is Caring", lines=16, max_lines=20)

    button.click(
        gradio_generate,
        inputs=[prompt, player, origin, gallery_zone],
        outputs=[art, report, commands, trace, profile, packet, canvas, value_json],
        api_name="generate_art",
    )


if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=int(os.getenv("PORT", "7860")),
    )
