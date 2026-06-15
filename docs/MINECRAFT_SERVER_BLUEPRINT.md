# Minecraft Server Blueprint

## Server Type

Use PebbleHost **8GB Budget Minecraft** for the first live demo.

Recommended settings:

- Paper server
- Minecraft `1.21.x`
- Java 21 if available
- Flat world
- Online mode enabled unless testing locally
- Whitelist enabled during build
- Advanced DDoS mitigation enabled

## Plugins

Minimum:

- WorldEdit
- DreamWall Paper Bridge

Optional:

- LuckPerms for role control
- CoreProtect for rollback/audit
- BlueMap or Dynmap if you want a web map preview

## World Shape

Flat world with one museum campus plus the existing public canvas as a secondary wing.

Suggested layout:

```text
spawn
  |
  +-- welcome board
  +-- AfterBlock Museum terminal
  +-- hall corridor
  +-- artifact pedestals/signs
  +-- DreamWall canvas wing at y=80
```

Coordinates:

```text
canvas origin: -192, 80, -192
plot size: 32
grid: 12 x 12
total canvas: 384 x 384 blocks
```

## Museum Rules

- Each submission gets a deterministic hall, zone, plot, and Minecraft coordinate.
- The server build must preserve the Space coordinate contract exactly:
  - `plot (0,0) -> XYZ -192 80 -192`
  - `plot (11,11) -> XYZ 160 80 160`
  - `world_x = -192 + plot_x * 32`
  - `world_z = -192 + plot_z * 32`
- Curation score replaces market value.
- Plaques show title, owner label, optional social tag, spirit first line, and hall.
- Resonance links connect nearby or emotionally similar artifacts.
- No real-money ownership, blockchain, or NFT claims.

## Built Campus Command

The Paper bridge includes a bounded museum builder:

```text
/dreamwall museum where
/dreamwall museum build
/dreamwall museum check
```

`/dreamwall museum build` creates the first live campus proof:

- 12 x 12 marked plot pads matching the Space's generated coordinates.
- Memory rails between plots so the campus reads as one living map, not isolated pedestals.
- Nine hall gates with colored banner markers.
- Entrance signage, a physical 12 x 12 entry atlas, and a `YOU ARE HERE` beacon.
- A verifier command that reports plot pads, relic focus blocks, entry beacon, and entry atlas presence from the actual world state.
- A clear import path: `/dreamwall import` places the generated packet on its exact plot pad and marks the atlas target, while `/dreamwall import here` remains the quick nearby proof.

## First Server Milestone

1. Buy server.
2. Install Paper and WorldEdit.
3. Upload DreamWall bridge jar.
4. Run `/dreamwall fetch`.
5. Run `/dreamwall pack` and accept the resource pack.
6. Run `/dreamwall museum build` once.
7. Run `/dreamwall museum check` and capture the `144/144` result plus the living entry atlas line.
8. Create a relic in the Space and show its generated plot/XYZ.
9. Run `/dreamwall import` to place the packet at `museum.coordinates`.
10. Record a 20-second proof clip from the `YOU ARE HERE` beacon to the placed relic.

## Museum Packet

The main demo packet is `dreamwall.museum.v1`.

It gives the server:

- artifact title
- owner label and optional social tag
- hall and zone
- plot and coordinates
- block palette/materials
- resource-pack model path and `CustomModelData`
- plaque text
- spirit first line
- passport QR payload
- curation scores and resonance links

The Paper plugin V1 only needs to import the packet and place a pedestal/sign/item marker at the coordinates. The Gradio `Artifact Model` preview, the resource-pack item JSON, and the server `CustomModelData` are intentionally the same proof chain.

## Texture Assets

The repo includes a generated resource-pack skeleton plus loose gallery textures:

```text
assets/afterblock_textures/items/
assets/afterblock_textures/gallery/index.html
resource-pack/AfterBlockMuseum/
```

The current pack includes 3,200 64x64 item textures, 3,200 3D item model JSON files, 3,200 `minecraft:paper` custom model data overrides, 70 object families, 10 material finishes, and six display profiles for pedestal, wall, tabletop, showcase, and handheld rendering.

V1 server proof can use `/dreamwall demo` to place a pedestal and give the player a Paper item with `CustomModelData 730002`. With the resource pack installed, that item renders as an AfterBlock relic.

## Living Canvas Packet

The secondary canvas packet is `living_canvas.mc.v1`.

It gives the server:

- stable tile coordinates
- per-tile `minecraft_origin`
- per-tile `minecraft_bounds`
- `stage`, `weather`, `value`, and `mutation_rate`
- `fusion_links` between tiles
- `evolution_events` for narration
- a `minecraft_animation_plan`

The wall does not need physical redstone for V1. Use the Space GIF as proof of motion, then represent motion in Minecraft with one of:

- animated map updates
- particles between linked tiles
- block-frame updates on a timer
- lamps or command-block pulses around high-stage artifacts

## Second Server Milestone

Implement real block placement from one `living_canvas.mc.v1` tile or one `dreamwall.mc.v1` `grid.row_runs` packet:

```text
world_x = canvas_origin_x + plot.x * 32 + run.x
world_y = 80 - run.y
world_z = canvas_origin_z + plot.z * 32
```

Then each row-run becomes a small `fill` operation.
