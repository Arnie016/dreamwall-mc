---
title: DreamWall AfterBlock Museum
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

# DreamWall: AfterBlock Museum

AfterBlock Museum is a Minecraft-native memory museum for the Build Small Hackathon.

Visitors scan a relic, memory, animal spirit, or prompted painting. The app assigns a museum hall, computes a curation score, awakens a tiny artifact spirit, prints a shareable passport card, and emits a `dreamwall.museum.v1` packet for the Minecraft server.

Living Graffiti and Living Moving Canvas remain as secondary modes. They power museum placement, resonance, and Minecraft wall mechanics.

The main cash-prize demo is now simple: relic -> hall -> spirit -> passport -> Minecraft museum placement.

The Gradio demo now opens with a clean museum preview: 100 labeled demo artifacts, nine hall wings, curation scores, coordinates, generated Minecraft-style item textures, and a live 3D artifact model tied to the same `CustomModelData` used by the server packet. Social tags are optional; if a visitor leaves the tag blank, the museum uses the owner name or anonymous label.

The main placement form accepts a visitor signature in the fourth field. A value like `@wildstash` becomes the hover/social tag; a plain value like `Arnav` becomes the owner label without adding a social badge.

The Space also includes a **Demo Path** tab with the critique, commands, and shot order for the three-minute hackathon video.

## Why This Is Different

Most hackathon apps stop at chat or image generation. AfterBlock turns language and memory into a place visitors can walk through.

- **Museum-native:** every input becomes an artifact with a hall, plaque, passport, and Minecraft coordinates.
- **Spirit-bearing:** each artifact awakens a constrained spirit that speaks only from its object and lore.
- **Resonance-based:** curation score replaces market/auction language.
- **Off-brand:** the Gradio app feels like a Minecraft museum terminal.
- **Rendered preview:** a floor-map image shows the museum populated with 100 demo artifacts.
- **3D artifact preview:** the selected relic renders in a Three.js cuboid scene inside Gradio, using the same model profile, material finish, and `CustomModelData` that the Minecraft bridge receives.
- **Less clutter:** the wall is organized by hall and by "when this becomes art" rather than dumping every relic as a noisy card grid.
- **Texture path:** 3,200 generated PNG textures plus 3,200 3D item model JSONs are generated for a Minecraft resource pack, with 70 object families and 10 material finishes.
- **Texture review links:** see `docs/TEXTURE_LINKS.md` for the searchable gallery, contact sheets, proofs, manifest, and resource-pack URLs.
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
- **Show, don't tell:** the demo is scan relic -> 3D artifact model -> hall placement -> passport -> Minecraft pedestal.

## Bonus Quests

- **Off-Brand:** custom Minecraft museum terminal UI styling.
- **Tiny Titan:** local deterministic semantic curator is far below the 32B limit and can be swapped for a <=4B model for the interpretation step.
- **Best Demo:** real object/prompt -> 3D preview -> passport -> server packet.
- **Community Choice:** passport cards are shareable and social tags are optional.
- **Sharing is Caring:** the app emits open museum and bridge packets for each artifact.
- **Field Notes:** see [`docs/FIELD_NOTES.md`](docs/FIELD_NOTES.md).

## Minecraft Server Layer

The MVP emits:

- WorldEdit-style row instructions
- a `dreamwall.museum.v1` artifact/passport/spirit packet
- a `living_graffiti.mc.v1` animated wall packet
- a `living_canvas.mc.v1` multi-prompt animated wall packet
- a `dreamwall.mc.v1` JSON bridge packet
- a `dreamwall.market.v1` demo valuation packet
- a `neuropets.mc.v1` creature spawn/simulation packet
- a named Gradio API endpoint: `generate_art`
- a named Gradio API endpoint: `hatch_pet`
- a named Gradio API endpoint: `living_graffiti`
- a named Gradio API endpoint: `living_canvas`
- a named Gradio API endpoint: `quick_curate`
- generated texture PNGs in `assets/afterblock_textures/items/`
- resource-pack skeleton in `resource-pack/AfterBlockMuseum/`
- searchable full texture gallery in `assets/afterblock_textures/gallery/index.html`
- Gradio Resource Pack Browser endpoint: `browse_textures`

Each `living_canvas.mc.v1` tile includes a stable `minecraft_origin` and `minecraft_bounds`, so the Paper bridge can place it directly on the 384x384 wall.

The repo also includes a Paper plugin scaffold in [`paper-plugin/`](paper-plugin/) that can reach the live Space and is ready to extend into block placement.

### API Shape

Use the Space API with the named endpoint:

```text
POST https://build-small-hackathon-dreamwall-mc.hf.space/gradio_api/call/quick_curate
```

Input order:

```json
[
  "white AirPods from my first year of university",
  "They carried private worlds through public noise during my first year away.",
  "@Wildstash",
  null
]
```

The final output is a plugin-ready museum packet with artifact title, hall, coordinates, palette/materials, resource-pack model path, `CustomModelData`, plaque text, spirit first line, optional social tag, owner label, and passport payload. The Paper bridge turns that packet into a placed relic, item hover lore, and a readable lectern passport in Minecraft.

## Design Docs

- [`docs/COMPETITION_GOAL.md`](docs/COMPETITION_GOAL.md)
- [`docs/MINECRAFT_SERVER_BLUEPRINT.md`](docs/MINECRAFT_SERVER_BLUEPRINT.md)
- [`docs/MUSEUM_CURATION.md`](docs/MUSEUM_CURATION.md)
- [`docs/TEXTURE_PACK_STRATEGY.md`](docs/TEXTURE_PACK_STRATEGY.md)
- [`docs/FIELD_NOTES.md`](docs/FIELD_NOTES.md)
- [`docs/HALL_PRESENTATION.md`](docs/HALL_PRESENTATION.md)
- [`docs/LIVING_GRAFFITI_MVP.md`](docs/LIVING_GRAFFITI_MVP.md)
- [`docs/NEUROPETS_MVP.md`](docs/NEUROPETS_MVP.md)
- [`docs/DEMO_RUNBOOK.md`](docs/DEMO_RUNBOOK.md)

## How This Can Win

DreamWall MC is aimed at **An Adventure in Thousand Token Wood** plus the **OpenAI Codex Track**.

Judging fit:

- **Genuinely delightful:** ordinary objects become Minecraft museum artifacts with tiny spirits.
- **AI is load-bearing:** semantic curation chooses halls, spirits, plaques, resonance, and placement.
- **Originality:** it is a memory museum ritual, not a chatbot wrapper.
- **Polish:** custom Gradio skin plus Minecraft bridge packet.
- **Visual worldbuilding:** the UI answers "when is this art?" through nine museum halls, not just "what object is this?"
- **Server parity:** the Gradio 3D preview, resource-pack item, and `dreamwall.museum.v1` packet point at the same artifact model.

Bonus quests:

- **Off-Brand:** custom UI beyond default Gradio.
- **Sharing is Caring:** open trace + server packet per generation.
- **Field Notes:** this repo includes [`docs/FIELD_NOTES.md`](docs/FIELD_NOTES.md).

Next high-impact demo step: use PebbleHost Paper to place one AfterBlock artifact pedestal/sign from the `dreamwall.museum.v1` packet, then record a 45-75 second video.

## Codex Track

This project is being built with Codex as the coding agent.

Public GitHub repo with Codex-attributed commits:

https://github.com/Arnie016/dreamwall-mc
