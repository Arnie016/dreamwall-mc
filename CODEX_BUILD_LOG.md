# Codex Build Log

This file records how Codex was used to build the hackathon entry.

## 2026-06-05

- Interpreted the Build Small Hackathon constraints and prize strategy.
- Chose the riskier `Adventure in Thousand Token Wood` track.
- Designed DreamWall MC as a Minecraft-native AI art wall.
- Scaffolded the Gradio Space MVP with:
  - prompt/player/gallery-zone input
  - tiny local semantic fingerprinting
  - Minecraft-style painting preview
  - block palette generation
  - WorldEdit/plugin instructions
  - open trace output for the `Sharing is Caring` badge
- Fixed the initial Hugging Face runtime error by adding Python 3.13 audio compatibility.
- Replaced the heavy Torch/sentence-transformers runtime with a fast local semantic fingerprint engine for a more reliable launch.
- Added a `generate_art` API endpoint and plugin-ready bridge packet for Minecraft server integration.
- Added a Paper plugin scaffold with `/dreamwall fetch` to test live Space connectivity from a Minecraft server.
- Expanded the concept into a flat-world canvas economy: plot assignment, creative fusion, demo-point valuation, voting/auction packet, and Minecraft server blueprint.
- Added NeuroPets mini version: prompt-to-creature hatchery, survival leaderboard, lineage wall, cooldown, and Minecraft spawn packet.
- Re-centered the cash-prize build around Living Graffiti: 10-frame animated Minecraft artifacts, mutation/fusion/value metadata, and a `living_graffiti.mc.v1` server packet.
- Improved Living Graffiti with prompt-derived names, explicit 32x32 block sizing, 10-frame footprint metadata, and staged growth from seed sketch to server myth.
- Added Living Moving Canvas mode: a multi-prompt 12x12 Minecraft wall simulation with neighbor fusion, attention weather, growth stages, and a `living_canvas.mc.v1` packet.
- Upgraded Living Moving Canvas into an animated wall: stable Minecraft coordinates, pulsing timeline frames, visible fusion links, evolution events, and a clearer Thousand Token Wood demo runbook.
