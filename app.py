import hashlib
import json
import math
import os
import tempfile
from dataclasses import dataclass

import gradio as gr
import numpy as np
from PIL import Image, ImageDraw


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
        "This is the Minecraft bridge as a social system: every prompt becomes a coordinate, neighbors create fusion pressure, and the wall has visible weather.",
        "",
        "Why this is the winning version:",
        "- It is Minecraft-native: coordinates, plots, wall slots, and server packets.",
        "- It is social: multiple people shape one shared canvas.",
        "- It is alive: mutation, growth stages, and attention weather change what the wall becomes.",
        "- It is demoable: the judge can see the wall, not just read a chatbot answer.",
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
  --mc-ink: #24170e;
  --mc-paper: #f4ecd8;
  --mc-green: #57744a;
  --mc-gold: #d39b45;
}
body, .gradio-container {
  background: #18130f !important;
  color: var(--mc-ink);
}
.gradio-container {
  max-width: 1180px !important;
}
.dreamwall-hero {
  background: linear-gradient(135deg, #f4ecd8 0%, #e5d0a3 100%);
  border: 3px solid #4a2f1f;
  box-shadow: 0 10px 0 #2a1a12;
  padding: 22px;
  margin: 14px 0 18px;
}
.dreamwall-hero h1 {
  margin: 0;
  font-size: 42px;
  color: #2a1a12;
}
.dreamwall-hero p {
  max-width: 760px;
  font-size: 17px;
  line-height: 1.45;
}
.badge-row span {
  display: inline-block;
  border: 2px solid #4a2f1f;
  background: #fff6dd;
  padding: 6px 10px;
  margin: 4px 5px 0 0;
  font-weight: 700;
}
textarea, input {
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace !important;
}
"""


with gr.Blocks(css=CSS, title="DreamWall MC") as demo:
    gr.HTML(
        """
        <section class="dreamwall-hero">
          <h1>Living Graffiti MC</h1>
          <p>
            Type a prompt, sign it, and mint a 10-frame Minecraft wall artifact.
            The artifact mutates, earns a wall slot, fuses with nearby ideas, and lives
            as a named public memory on the server.
          </p>
          <div class="badge-row">
            <span>Adventure in Thousand Token Wood</span>
            <span>OpenAI Codex Track</span>
            <span>Off-Brand</span>
            <span>Best Demo</span>
            <span>Sharing is Caring</span>
            <span>Field Notes</span>
          </div>
        </section>
        """
    )
    gr.HTML("<h2>Living Graffiti Wall</h2>")
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
    demo.load(
        living_graffiti,
        inputs=[graffiti_prompt, graffiti_player, graffiti_zone],
        outputs=[graffiti_gif, graffiti_story, graffiti_canvas, graffiti_packet],
    )

    gr.HTML("<h2>Living Moving Canvas</h2>")
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
    demo.load(
        living_wall_canvas,
        inputs=[wall_prompts, wall_zone, wall_tick],
        outputs=[wall_image, wall_story, wall_packet],
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
    demo.load(
        hatch_neuropet,
        inputs=[pet_prompt, pet_player, pet_island],
        outputs=[pet_image, pet_card, pet_leaders, pet_lineage, pet_packet],
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
    demo.load(
        gradio_generate,
        inputs=[prompt, player, origin, gallery_zone],
        outputs=[art, report, commands, trace, profile, packet, canvas, value_json],
    )


if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=int(os.getenv("PORT", "7860")),
    )
