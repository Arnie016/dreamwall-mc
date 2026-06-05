import hashlib
import json
import math
import os
from dataclasses import dataclass
from functools import lru_cache

import gradio as gr
import numpy as np
from PIL import Image, ImageDraw
from sentence_transformers import SentenceTransformer


MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"
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


@dataclass
class ArtResult:
    image: Image.Image
    profile: dict
    palette: list
    commands: str
    report: str
    trace: str


@lru_cache(maxsize=1)
def model():
    return SentenceTransformer(MODEL_ID)


def stable_seed(text: str) -> int:
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return int(digest[:16], 16)


def embedding(text: str) -> np.ndarray:
    vec = model().encode([text], normalize_embeddings=True)[0]
    return np.asarray(vec, dtype=np.float32)


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
            "parameter_count": "22M embedding model, far below 32B",
            "prompt": prompt,
            "player": player,
            "gallery_zone": gallery_zone,
            "moods": moods,
            "palette": palette_names,
        },
        indent=2,
    )
    commands = compact_commands(grid, palette, origin)
    return ArtResult(image, profile, palette_names, commands, report, trace)


def gradio_generate(prompt: str, player: str, origin: str, gallery_zone: str):
    result = make_art(prompt, player, origin, gallery_zone)
    return (
        result.image,
        result.report,
        result.commands,
        result.trace,
        result.profile,
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
        profile = gr.JSON(label="Artist fingerprint")
    with gr.Tabs():
        with gr.Tab("WorldEdit / Plugin Plan"):
            commands = gr.Code(label="Mural instructions", language="shell", lines=18)
        with gr.Tab("Open Trace"):
            trace = gr.Code(label="Trace for Sharing is Caring", language="json", lines=16)

    button.click(
        gradio_generate,
        inputs=[prompt, player, origin, gallery_zone],
        outputs=[art, report, commands, trace, profile],
    )
    demo.load(
        gradio_generate,
        inputs=[prompt, player, origin, gallery_zone],
        outputs=[art, report, commands, trace, profile],
    )


if __name__ == "__main__":
    demo.launch()
