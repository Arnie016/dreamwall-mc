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
- Added per-tile Minecraft origins/bounds and documented the Paper bridge path for placing Living Canvas tiles and representing motion through particles, map updates, or block-frame updates.
- Reframed the project as DreamWall: AfterBlock Museum with `dreamwall.museum.v1`, deterministic hall placement, curation scores, artifact spirits, passport cards, seeded relic demos, museum-terminal UI, and a GitHub Actions Paper plugin build workflow.
- Expanded AfterBlock assets into a resource-pack pipeline: 1,200 generated item textures, 1,200 3D model JSONs, custom model data overrides, contact-sheet screenshots, a browser gallery, and a `/dreamwall demo` Paper command for an in-game pedestal proof.
- Added `/dreamwall import` and `/dreamwall import here` to the Paper bridge. The plugin now calls the live Gradio `curate_artifact` endpoint, parses `dreamwall.museum.v1`, and places a packet-derived pedestal/sign/item in Minecraft.
- Added Gson shading plus explicit Maven Central resolution so the Paper jar compiles into a self-contained PebbleHost-friendly plugin.
- Verified the shaded jar locally with temporary Maven 3.9.9 and prepared an ignored deploy bundle at `dist/pebblehost/` with the plugin jar, `AfterBlockMuseum.zip`, and hashes.
