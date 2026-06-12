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
- Curation score replaces market value.
- Plaques show title, owner handle, spirit first line, and hall.
- Resonance links connect nearby or emotionally similar artifacts.
- No real-money ownership, blockchain, or NFT claims.

## First Server Milestone

1. Buy server.
2. Install Paper and WorldEdit.
3. Upload DreamWall bridge jar.
4. Run `/dreamwall fetch`.
5. Call the `curate_artifact` Space endpoint and copy the `dreamwall.museum.v1` packet.
6. Manually place one pedestal/sign at `museum.coordinates`.
7. Add signs for title, owner handle, hall, plaque line, and spirit first line.
8. Record a 20-second proof clip.

## Museum Packet

The main demo packet is `dreamwall.museum.v1`.

It gives the server:

- artifact title
- owner handle
- hall and zone
- plot and coordinates
- block palette/materials
- plaque text
- spirit first line
- passport QR payload
- curation scores and resonance links

The Paper plugin V1 only needs to import the packet and place a pedestal/sign/painting marker at the coordinates.

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
