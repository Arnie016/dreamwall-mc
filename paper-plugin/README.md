# DreamWall AfterBlock Paper Bridge

This is the Minecraft server bridge for DreamWall: AfterBlock Museum.

The hackathon Space is the official submission surface. This plugin scaffold is the live-demo layer: it connects a Paper server to the Space API and prepares the path for placing generated wall art inside Minecraft.

## Current Demo Behavior

- `/dreamwall` shows the configured Space endpoint.
- `/dreamwall fetch` calls the Space app domain and confirms the bridge can reach Hugging Face.
- `/dreamwall pack` asks the player client to load the Hugging Face-hosted `AfterBlockMuseum.zip` resource pack.
- `/dreamwall demo` places a safe local pedestal/sign proof, spawns an `ItemDisplay` relic, and gives the player a Paper item with `CustomModelData 730002`.
- `/dreamwall import` calls the live `quick_curate` Gradio endpoint, parses the returned `dreamwall.museum.v1` packet, and places a packet-derived pedestal/sign/`ItemDisplay`/item at the artifact coordinates.
- `/dreamwall import here` uses the same live packet but places it two blocks in front of the player for fast video proof.
- `/dreamwall museum where` prints the coordinate contract used by the Space and server.
- `/dreamwall museum build` creates the 12 x 12 living museum campus at the configured origin, with plot pads, memory rails, hall gates, banner markers, and a `YOU ARE HERE` entry.
- `/dreamwall museum check` verifies that all 144 plot pads, relic focus blocks, and the entry beacon exist in the current world.
- A scheduled task can be extended to poll approved museum artifacts.
- The Space now emits `dreamwall.museum.v1`, the main AfterBlock packet for the hackathon demo.
- The Space also emits `living_canvas.mc.v1` for the secondary wall/canvas mode.

## Planned Placement Behavior

The main Space endpoint is `quick_curate`, which emits `dreamwall.museum.v1` with:

- artifact title
- owner handle
- hall and zone
- plot and coordinates
- block palette/materials
- plaque text
- spirit first line
- passport QR payload
- curation scores
- resonance links

Implemented `/dreamwall import` V1 behavior:

1. Fetch latest artifact packet.
2. Place pedestal/sign/painting marker at coordinates.
3. Display plaque line and owner handle.
4. Optionally create particles or a simple animation based on artifact type.

The legacy `generate_art` endpoint emits a `dreamwall.mc.v1` JSON packet with:

- `job_id`
- `player`
- `prompt`
- `gallery_zone`
- `origin`
- `palette`
- `plot`
- `market`
- `grid.row_runs`
- WorldEdit preview lines

The secondary canvas path uses `living_canvas.mc.v1` from the `living_canvas` endpoint:

- `tile_size_blocks`: `32 x 32`
- `canvas_size_tiles`: `12 x 12`
- `minecraft_wall_size_blocks`: `384 x 384`
- `tiles[].minecraft_origin`
- `tiles[].minecraft_bounds`
- `tiles[].stage`
- `tiles[].weather`
- `fusion_links`
- `evolution_events`
- `minecraft_animation_plan`

The plugin should treat each tile as a stable wall address. Motion comes from particles, map updates, or block-frame updates, not from moving the artifact to a new plot.

The next plugin step is converting `grid.row_runs` into wall block placement:

```text
origin + (x, -y, 0) -> block
```

The Space also emits a `neuropets.mc.v1` packet from the `hatch_pet` endpoint. The server can use it to create:

- named creature sign
- armor stand / mob placeholder
- habitat marker
- particle effect
- leaderboard entry

For the hackathon video, the safest route is:

1. Run AfterBlock Museum in the Space.
2. Copy the `dreamwall.museum.v1` packet or call the Gradio API.
3. Place one artifact pedestal/sign at `museum.coordinates`.
4. Add signs for owner, title, hall, plaque, and spirit first line.
5. Use particles around the pedestal for the artifact spirit.
6. Walk through the museum gallery.

## Flat World Canvas

Recommended V1 canvas:

- Flat Paper world
- `12 x 12` plots
- `32 x 32` blocks per plot
- Canvas origin: `-192, 80, -192`
- Use signs or floating text later for creator, prompt, value, and fusion history.

The Space assigns the plot. The plugin should trust the packet and place the mural at:

```text
canvas_origin + plot.x * plot_size, y=80, canvas_origin_z + plot.z * plot_size
```

For `living_canvas.mc.v1`, the packet already includes `tiles[].minecraft_origin`, so the plugin can skip recomputing the address.

## Build

GitHub Actions builds the jar through `.github/workflows/build-plugin.yml`.

Local build, if Maven is installed:

```bash
mvn package
```

The jar will be in `target/dreamwall-paper-bridge-0.1.0.jar`.

## Install

1. Stop the PebbleHost Paper server.
2. Upload the jar to `plugins/`.
3. Upload or link the `resource-pack/AfterBlockMuseum/` zip as a server resource pack if you want custom item rendering. The default config can also request the Hugging Face-hosted pack with `/dreamwall pack`.
4. Start the server.
5. Edit `plugins/DreamWall/config.yml` if needed.
6. Run `/dreamwall fetch` in game or console.
7. Run `/dreamwall pack` in game and accept the resource pack.
8. Run `/dreamwall museum build` once to create the coordinate-accurate museum campus.
9. Run `/dreamwall museum check` to confirm the built world matches the Space coordinate map.
10. Run `/dreamwall demo` in game to place a pedestal proof, visible `ItemDisplay`, and receive the AirPods demo item.
11. Run `/dreamwall import` to place a live Hugging Face artifact packet at its generated plot, or `/dreamwall import here` for a nearby proof.

## Local Server Proof

Codex verified the plugin in a temporary Paper server:

```text
Paper 1.21.4 build 232
Java Temurin 21.0.11
commands: dreamwall, dreamwall fetch, dreamwall pack, stop
```

Proof artifact:

```text
artifacts/stress/paper_plugin_local_load_test.json
```
