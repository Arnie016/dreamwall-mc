---
title: DreamWall MC
emoji: 🧱
colorFrom: yellow
colorTo: green
sdk: gradio
sdk_version: 5.29.0
python_version: "3.10"
app_file: app.py
pinned: false
license: apache-2.0
tags:
  - minecraft
  - gradio
  - small-models
  - art
  - game
  - agent-trace
  - codex
---

# DreamWall MC

DreamWall MC is a Minecraft-native AI art wall for the Build Small Hackathon.

Players type a short prompt and sign it with their player name. A tiny local semantic fingerprint engine turns the prompt, player signature, and wall zone into a Minecraft-style painting preview, a block palette, a plot on a public canvas, and WorldEdit/plugin instructions for placing the art into a shared server gallery.

The fun part is drift: tiny wording changes and different player names visibly change the painting. Nearby prompts can fuse into shared concepts, and each plot gets a demo value based on density, adjacency, rarity, and votes. The wall acts like a shared server memory rather than a normal image generator.

## Why This Is Different

Most hackathon apps stop at chat or image generation. DreamWall MC turns language into a shared place.

- **Minecraft-native:** the output is a wall packet, block palette, and row-run placement plan, not just a picture.
- **Identity-aware:** the same prompt changes when the player signature or gallery zone changes.
- **Social artifact:** every prompt becomes part of a public server museum.
- **Creative fusion:** nearby concepts combine into more valuable artifacts.
- **Value without compliance risk:** auction/voting uses demo points, not real money or blockchain.
- **Small by design:** no giant remote model API is required for the core experience.
- **Demo-first:** the video can show prompt -> Space preview -> Minecraft wall/gallery.

## Hackathon Fit

- **Track:** An Adventure in Thousand Token Wood
- **Small model constraint:** the app uses a local semantic fingerprint engine, far below the 32B limit, with no cloud API dependency.
- **Built on Gradio:** this Space is the official Gradio submission surface.
- **Show, don't tell:** the demo is prompt -> painting -> Minecraft wall plan.

## Bonus Quests

- **Off-Brand:** custom Minecraft/map-wall UI styling.
- **Sharing is Caring:** the app emits an open trace for each painting.
- **Field Notes:** see `FIELD_NOTES.md`.

## Minecraft Server Layer

The MVP emits:

- WorldEdit-style row instructions
- a `dreamwall.mc.v1` JSON bridge packet
- a `dreamwall.market.v1` demo valuation packet
- a named Gradio API endpoint: `generate_art`

The repo also includes a Paper plugin scaffold in [`paper-plugin/`](paper-plugin/) that can reach the live Space and is ready to extend into block placement.

### API Shape

Use the Space API with the named endpoint:

```text
POST https://build-small-hackathon-dreamwall-mc.hf.space/gradio_api/call/generate_art
```

Input order:

```json
[
  "a tiny fox wizard guarding a ruined ocean temple",
  "ArnavS",
  "~ ~ ~",
  "moss wing, west wall"
]
```

The final output is a plugin-ready JSON packet with `job_id`, `player`, `prompt`, `palette`, `grid.row_runs`, and placement hints.

## Design Docs

- [`docs/COMPETITION_GOAL.md`](docs/COMPETITION_GOAL.md)
- [`docs/MINECRAFT_SERVER_BLUEPRINT.md`](docs/MINECRAFT_SERVER_BLUEPRINT.md)
- [`docs/CANVAS_ECONOMY.md`](docs/CANVAS_ECONOMY.md)
- [`docs/DEMO_RUNBOOK.md`](docs/DEMO_RUNBOOK.md)

## How This Can Win

DreamWall MC is aimed at **An Adventure in Thousand Token Wood** plus the **OpenAI Codex Track**.

Judging fit:

- **Genuinely delightful:** a shared Minecraft museum where language becomes wall art.
- **AI is load-bearing:** semantic drift and identity fingerprinting change the artifact.
- **Originality:** it is a server ritual, not a chatbot wrapper.
- **Polish:** custom Gradio skin plus Minecraft bridge packet.

Bonus quests:

- **Off-Brand:** custom UI beyond default Gradio.
- **Sharing is Caring:** open trace + server packet per generation.
- **Field Notes:** this repo includes `FIELD_NOTES.md`.

Next high-impact demo step: use PebbleHost Paper + the bridge plugin to place one generated packet on a real wall, then record a 30-45 second video.

## Codex Track

This project is being built with Codex as the coding agent.

Public GitHub repo with Codex-attributed commits:

https://github.com/Arnie016/dreamwall-mc
