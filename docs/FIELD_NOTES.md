# Why I Built a Minecraft Museum for Small Memories

## Problem

Most AI demos make a result and then let it disappear into a chat history or download folder. That felt wrong for personal objects. A book, a charger, a school bag, a pair of AirPods, or a prompted painting can carry real identity, but normal generators flatten those things into one more image.

AfterBlock Museum treats small memories as things worth placing. The output is not just text or art. It is a named artifact with a hall, a plaque, a spirit line, a passport card, and permanent Minecraft coordinates.

## Why Minecraft

Minecraft makes memory spatial. A judge can understand the loop immediately:

1. Describe or upload a relic.
2. The museum curates it into a hall.
3. A passport card appears.
4. A bridge packet can place the relic in a shared Minecraft world.

That gives the demo a physical destination. The Hugging Face Space is the museum terminal; the Minecraft server is the place where artifacts live.

## Why Small Models

The hackathon asks for small, joyful systems rather than giant wrappers. AfterBlock uses a tiny deterministic semantic fingerprint pipeline for the core demo:

- prompt and memory interpretation
- mood and palette selection
- hall placement
- curation scoring
- object-spirit lines
- stable plot and coordinate assignment
- Minecraft bridge packet generation

The current fallback is local and deterministic, so the demo does not break if an external model is unavailable. The architecture leaves a clean slot for a tiny text or vision model to replace the interpretation step without changing the museum packet.

## Competition Landscape

Education projects are useful. Emotional garden projects are warm. Generated-world projects are delightful. Agent-economy projects are technically interesting.

AfterBlock tries to defend a different lane: real or imagined objects become preserved, owner-linked, Minecraft-native artifacts. The emotional layer is not abstract encouragement; it is attached to coordinates, materials, model data, and a playable server bridge.

## Design Choices

- Avoid market, auction, and blockchain language.
- Use curation, resonance, visitor echoes, and memory weight instead.
- Keep one simple museum prompt for the main demo.
- Hide advanced controls behind accordions.
- Make the UI feel like a Minecraft museum terminal rather than a default AI form.
- Generate many reviewable Minecraft assets, but expose them through a searchable gallery and Gradio inspection wall.

## What Works Now

- `dreamwall.museum.v1` artifact packets.
- `dreamwall.mc.v1` bridge fields for title, hall, owner, coordinates, materials, plaque, spirit line, QR payload, and CustomModelData.
- Five deterministic seeded demos.
- A 3,200-item resource pack with PNG textures, 3D item model JSON, 70 object families, 10 material finishes, and six display profiles.
- Shareable passport-card HTML.
- A trace dataset at `data/artifact_traces.jsonl`.

## What Is Next

The next proof should happen inside Minecraft: load the resource pack, run the Paper bridge, import one artifact, and record a short walk-through showing the object, plaque, owner handle, spirit line, and item rendering in-world.
