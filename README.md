---
title: Living Graffiti MC
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

# Living Graffiti MC

Living Graffiti MC is a Minecraft-native living canvas for the Build Small Hackathon.

Players type a prompt, sign it, and get a named 10-frame Minecraft-style animated wall artifact. Each artifact is designed as a **32x32 block wall tile** with **1,024 blocks per frame**, a wall slot, mutation rate, growth stage, fusion/value readout, creator credit, and a `living_graffiti.mc.v1` packet for the Minecraft server.

The next-level mode is a shared moving canvas: multiple people's prompts claim stable coordinates on a 12x12 Minecraft wall, pulse through timeline ticks, mutate with attention weather, draw visible fusion links with nearby ideas, and export a `living_canvas.mc.v1` server packet.

NeuroPets and DreamWall remain as secondary modes, but the main cash-prize demo is now simple: imagination feed -> living canvas -> fusion/value -> Minecraft public wall.

## Why This Is Different

Most hackathon apps stop at chat or image generation. Living Graffiti turns language into a shared animated place.

- **Animated:** each prompt becomes a 10-frame artifact, not a static image.
- **Grows:** artifacts unlock stages from seed sketch to server myth based on value and mutation.
- **Collective:** many prompts become one shared moving canvas, not isolated images.
- **Alive:** the wall has attention weather, timeline ticks, fusion links, and growth stages: myth storm, mutation wind, fusion bloom, quiet ruins, and steady glow.
- **Minecraft-native:** the output is a wall packet, block palette, and row-run placement plan, not just a picture.
- **Creature-native:** prompts hatch named pets with survival odds, lineage, and server state.
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
- a `living_graffiti.mc.v1` animated wall packet
- a `living_canvas.mc.v1` multi-prompt animated wall packet
- a `dreamwall.mc.v1` JSON bridge packet
- a `dreamwall.market.v1` demo valuation packet
- a `neuropets.mc.v1` creature spawn/simulation packet
- a named Gradio API endpoint: `generate_art`
- a named Gradio API endpoint: `hatch_pet`
- a named Gradio API endpoint: `living_graffiti`
- a named Gradio API endpoint: `living_canvas`

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
- [`docs/LIVING_GRAFFITI_MVP.md`](docs/LIVING_GRAFFITI_MVP.md)
- [`docs/NEUROPETS_MVP.md`](docs/NEUROPETS_MVP.md)
- [`docs/DEMO_RUNBOOK.md`](docs/DEMO_RUNBOOK.md)

## How This Can Win

DreamWall MC is aimed at **An Adventure in Thousand Token Wood** plus the **OpenAI Codex Track**.

Judging fit:

- **Genuinely delightful:** a shared Minecraft wall where language becomes a living, moving canvas.
- **AI is load-bearing:** semantic drift and identity fingerprinting change the artifact.
- **Originality:** it is a server ritual, not a chatbot wrapper.
- **Polish:** custom Gradio skin plus Minecraft bridge packet.

Bonus quests:

- **Off-Brand:** custom UI beyond default Gradio.
- **Sharing is Caring:** open trace + server packet per generation.
- **Field Notes:** this repo includes `FIELD_NOTES.md`.

Next high-impact demo step: use PebbleHost Paper to show the 384x384 Living Moving Canvas wall with one named 32x32 slot placed from the packet, then record a 30-45 second video.

## Codex Track

This project is being built with Codex as the coding agent.

Public GitHub repo with Codex-attributed commits:

https://github.com/Arnie016/dreamwall-mc
