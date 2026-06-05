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

Players type a short prompt and sign it with their player name. A tiny local semantic fingerprint engine turns the prompt, player signature, and wall zone into a Minecraft-style painting preview, a block palette, and WorldEdit/plugin instructions for placing the art into a shared server gallery.

The fun part is drift: tiny wording changes and different player names visibly change the painting. The wall acts like a shared server memory rather than a normal image generator.

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

The MVP emits WorldEdit-style row instructions. The planned live demo layer is a Paper plugin that polls approved DreamWall jobs and places them into an item-frame/map-art gallery or a block mosaic wall.

## Codex Track

This project is being built with Codex as the coding agent.

Public GitHub repo with Codex-attributed commits:

https://github.com/Arnie016/dreamwall-mc
