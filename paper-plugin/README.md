# DreamWall Paper Bridge

This is the Minecraft server bridge for DreamWall MC.

The hackathon Space is the official submission surface. This plugin scaffold is the live-demo layer: it connects a Paper server to the Space API and prepares the path for placing generated wall art inside Minecraft.

## Current Demo Behavior

- `/dreamwall` shows the configured Space endpoint.
- `/dreamwall fetch` calls the Space app domain and confirms the bridge can reach Hugging Face.
- A scheduled task can be extended to poll approved wall jobs.

## Planned Placement Behavior

The Space emits a `dreamwall.mc.v1` JSON packet with:

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

1. Generate art in the Space.
2. Copy the bridge packet or call the Gradio API.
3. Use the Paper plugin to place the packet at a fixed gallery wall.
4. Walk through the server gallery.

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

## Build

```bash
mvn package
```

The jar will be in `target/dreamwall-paper-bridge-0.1.0.jar`.

## Install

1. Stop the PebbleHost Paper server.
2. Upload the jar to `plugins/`.
3. Start the server.
4. Edit `plugins/DreamWall/config.yml` if needed.
5. Run `/dreamwall fetch` in game or console.
