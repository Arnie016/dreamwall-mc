import hashlib
import json
import math
import os
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
          <h1>DreamWall MC</h1>
          <p>
            A tiny Minecraft art ritual: type a sentence, sign it with a player name,
            and a small model turns it into a public wall painting, palette, and build plan.
            Tiny wording changes create different artifacts.
          </p>
          <div class="badge-row">
            <span>Adventure in Thousand Token Wood</span>
            <span>Off-Brand</span>
            <span>Sharing is Caring</span>
            <span>Field Notes</span>
          </div>
        </section>
        """
    )
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
