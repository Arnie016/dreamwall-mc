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

Flat world with one giant public canvas.

Suggested layout:

```text
spawn
  |
  +-- welcome board
  +-- rules board
  +-- DreamWall canvas at y=80
  +-- 12x12 plot grid
  +-- each plot is 32x32 blocks
```

Coordinates:

```text
canvas origin: -192, 80, -192
plot size: 32
grid: 12 x 12
total canvas: 384 x 384 blocks
```

## Plot Rules

- Each submission gets a deterministic plot from prompt + player + gallery zone.
- Nearby plots can fuse if their symbols/moods align.
- Names are shown as signs or hologram-style text later.
- Value is demo points, not real money.

## First Server Milestone

1. Buy server.
2. Install Paper and WorldEdit.
3. Upload DreamWall bridge jar.
4. Run `/dreamwall fetch`.
5. Manually place one generated row-run mural on a test wall.
6. Record a 20-second proof clip.

## Second Server Milestone

Implement real block placement from `grid.row_runs`:

```text
world_x = canvas_origin_x + plot.x * 32 + run.x
world_y = 80 - run.y
world_z = canvas_origin_z + plot.z * 32
```

Then each row-run becomes a small `fill` operation.
