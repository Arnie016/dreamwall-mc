# PebbleHost Deployment Checklist

This is the shortest path to make the AfterBlock Museum demo visible in a live Minecraft server.

## Local Build Artifacts

Build the Paper plugin:

```bash
/tmp/apache-maven-3.9.9/bin/mvn -q -f paper-plugin/pom.xml package
```

Prepared local bundle:

```text
dist/pebblehost/dreamwall-paper-bridge-0.1.0.jar
dist/pebblehost/AfterBlockMuseum.zip
dist/pebblehost/afterblock-demo-world.zip
dist/pebblehost/SHA256SUMS
```

Current hashes from the verified local bundle:

```text
e6b53404d28a26732f0d28398d81b47e465045e7e4286039c6346c2d302a4148  AfterBlockMuseum.zip
ab8e91785e2e487d5267906a1a825bf3472a7abc3e19c71d20cb7fd3c0f666b2  dreamwall-paper-bridge-0.1.0.jar
6c789a5ec618c76860a8a8450a351b29280958f863945e3df571498a423f7c3e  afterblock-demo-world.zip
```

## Upload Targets

Upload with SFTP or the PebbleHost file manager:

```text
plugins/dreamwall-paper-bridge-0.1.0.jar
AfterBlockMuseum.zip
```

Credential-safe helper:

```bash
PEBBLEHOST_SFTP_USER="your-panel-sftp-username" bash scripts/pebblehost_upload.sh
```

Preview without connecting:

```bash
PEBBLEHOST_SFTP_USER="your-panel-sftp-username" bash scripts/pebblehost_upload.sh --dry-run
```

The helper uses the known SFTP host and username, prints local SHA256 hashes, prompts for the PebbleHost panel password through `sftp`, and uploads:

```text
plugins/dreamwall-paper-bridge-0.1.0.jar
AfterBlockMuseum.zip
afterblock-demo-world.zip
afterblock-SHA256SUMS.txt
```

Optional shortcut for demo servers: unzip `afterblock-demo-world.zip` into the server root before restart. It contains the locally verified `world`, `world_nether`, `world_the_end`, and `server.properties` from the smoke test.

The known PebbleHost SFTP endpoint from the account screen was:

```text
sftp://uk144.pebblehost.net:2222
```

Use the PebbleHost panel username/password. Do not commit credentials.

## Server Resource Pack

In the PebbleHost panel or `server.properties`, set the server resource pack URL to a downloadable URL for:

```text
AfterBlockMuseum.zip
```

The plugin also includes this default Hugging Face-hosted pack URL:

```text
https://huggingface.co/spaces/build-small-hackathon/dreamwall-mc/resolve/main/resource-pack/AfterBlockMuseum.zip
```

Run `/dreamwall pack` in-game to ask the client to load that pack. The current SHA1 for Minecraft's resource-pack hash is:

```text
42738bc973abb6a631bd9ba88ed3b2d7e8521800
```

Set `offer-resource-pack-on-join: true` in `plugins/DreamWall/config.yml` only if you want the server to offer it automatically when players join.

The pack contains:

```text
3,200 PNG item textures
3,200 item model JSON files
3,200 CustomModelData overrides on minecraft:paper
70 object families
10 material finishes
6 variant display profiles for pedestal, wall, tabletop, showcase, and handheld rendering
```

## In-Game Smoke Test

After restarting the server, run these as an op player:

```text
/dreamwall
/dreamwall fetch
/dreamwall pack
/dreamwall museum where
/dreamwall museum build
/dreamwall museum check
/dreamwall demo
/dreamwall import here
```

Expected result:

- `/dreamwall fetch` reports the Hugging Face Space is reachable.
- `/dreamwall pack` asks the player to load `AfterBlockMuseum.zip`.
- `/dreamwall museum where` prints the exact Space-to-world coordinate formula.
- `/dreamwall museum build` creates the 12 x 12 AfterBlock campus: plot pads, hall gates, banner markers, entrance signage, and a `YOU ARE HERE` beacon.
- `/dreamwall museum check` confirms the current world contains 144 plot pads, 144 relic focus blocks, and the entry beacon.
- `/dreamwall demo` places a small pedestal, sign, visible `ItemDisplay`, lectern passport book, and gives a Paper item using `CustomModelData 730002`.
- `/dreamwall import here` calls the live `quick_curate` endpoint, parses `dreamwall.museum.v1`, places a packet-derived pedestal/sign/`ItemDisplay`/lectern passport beside the player, and gives a Paper item using the packet's `custom_model_data`.
- `/dreamwall import` places the packet-derived artifact at the generated museum coordinates, paints a lit route from the `YOU ARE HERE` entry to that plot, sets the player's compass target, and gives a named route compass. The coordinate contract is `x = -192 + plot_x * 32`, `y = 80`, `z = -192 + plot_z * 32`.

If the Paper item looks like ordinary paper, the plugin is working but the resource pack is not loaded.

For the three-minute video, the best proof order is:

1. Create a relic in the Space and show the passport/packet coordinate.
2. Join the Paper server and run `/dreamwall museum build`.
3. Run `/dreamwall museum check` to prove the map exists.
4. Run `/dreamwall import` so the same relic appears at the exact generated plot and updates the route trail.
5. Hold the route compass, then walk from the `YOU ARE HERE` beacon along the lit floor route to the plot pad and show the resource-pack item.

## Local Proof

Codex verified the plugin boots on Paper before PebbleHost install:

```text
Paper 1.21.11 build 127
Java Temurin 21.0.11
DreamWall enabled
dreamwall fetch reached the Hugging Face Space
dreamwall pack printed the public pack URL and SHA1
dreamwall museum check reported 144/144 pads after a clean restart
```

Proof file:

```text
artifacts/stress/paper_plugin_local_load_test.json
```
