# PebbleHost Deployment Checklist

This is the shortest path to make the AfterBlock Museum demo visible in a live Minecraft server.

## Local Build Artifacts

The Space and `server-kit/` include a prebuilt Paper plugin. To rebuild it locally on a machine with Maven:

```bash
mvn -q -f paper-plugin/pom.xml package
```

Prepared local bundle:

```text
dist/pebblehost/dreamwall-paper-bridge-0.1.0.jar
dist/pebblehost/AfterBlockMuseum.zip
dist/pebblehost/afterblock-demo-world.zip
dist/pebblehost/SHA256SUMS
```

The Hugging Face Space also serves a complete Paper server kit from the `Minecraft Server` tab. That ZIP includes:

```text
plugins/dreamwall-paper-bridge-0.1.0.jar
plugins/DreamWall/config.yml
AfterBlockMuseum.zip
server.properties.append
README.md
```

In that tab, set the default import prompt, story, and visitor signature before downloading the ZIP if `/dreamwall import` should place a specific demo relic.

Current hashes from the verified local bundle:

```text
4e707a6ee065be5476d300f77bf6d05b382e9dddb8b43a8e8bb13b84dfc44cf5  AfterBlockMuseum.zip
35aeae59268cef96c50f7757451455db5cce30804aa1bd4738532d4d5601762a  dreamwall-paper-bridge-0.1.0.jar
33edcf48d00eca44e8076e5f62f5e3289c6686aecbf24e80349e9a6c2f7ed1f3  afterblock-demo-world.zip
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

Optional shortcut for demo servers: unzip `afterblock-demo-world.zip` into the server root before restart. It contains the locally verified `world`, `world_nether`, and `world_the_end` folders with the memory-spine museum already built; it intentionally does not overwrite `server.properties`.

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
03487f018e2062e254b5ea443396f29d099f8b67
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
- `/dreamwall museum build` creates the 12 x 12 AfterBlock campus: plot pads, hall gates, banner markers, a central memory spine, entrance signage, and a `YOU ARE HERE` beacon.
- `/dreamwall museum check` confirms the current world contains 144 plot pads, 144 relic focus blocks, and the entry beacon.
- `/dreamwall demo` places a small pedestal, visible `ItemDisplay`, glowing engraved name/caption, lectern passport book, right-click profile button, and gives a Paper item using `CustomModelData 730002`.
- `/dreamwall import here` calls the live `quick_curate` endpoint, parses `dreamwall.museum.v1`, places a packet-derived pedestal/`ItemDisplay`/engraved nameplate/lectern passport/profile button beside the player, and gives a Paper item using the packet's `custom_model_data`.
- `/dreamwall import` places the packet-derived artifact at the generated museum coordinates, paints a lit route from the `YOU ARE HERE` entry to that plot, persists a right-click profile button for the relic history, sets the player's compass target, and gives a named route compass. The coordinate contract is `x = -192 + plot_x * 32`, `y = 80`, `z = -192 + plot_z * 32`.

If the Paper item looks like ordinary paper, the plugin is working but the resource pack is not loaded.

For the three-minute video, the best proof order is:

1. Create a relic in the Space and show the passport/packet coordinate.
2. Join the Paper server and run `/dreamwall museum build`.
3. Run `/dreamwall museum check` to prove the map exists.
4. Run `/dreamwall import` so the same relic appears at the exact generated plot and updates the route trail.
5. Hold the route compass, walk from the `YOU ARE HERE` beacon along the lit floor route to the plot pad, show the resource-pack item and engraved nameplate, then right-click the profile button for the relic history.

## Local Proof

Run the current packaged-demo verifier before recording or uploading:

```bash
.venv/bin/python tools/verify_afterblock_demo.py
```

It emits:

```text
artifacts/stress/afterblock_demo_proof_manifest.json
```

That manifest verifies the current Space-to-Paper contract: 13-output `Place in Museum` flow, visible live Paper handoff, per-relic server kit ZIP contents, 3,200 textures, 3,200 item models, 3,200 `minecraft:paper` overrides, plugin/world checksums, the 12 x 12 / 144-plot coordinate contract, and the password-gated PebbleHost upload step.

Codex verified the plugin boots on Paper before PebbleHost install:

```text
Paper 1.21.4 build 232
Java Temurin 21.0.11
DreamWall enabled
dreamwall fetch reached the Hugging Face Space
dreamwall pack printed the public pack URL and SHA1
dreamwall museum check reported 144/144 pads after a clean restart
post-engraving jar loaded and dreamwall museum check still reported 144/144 pads
```

Proof file:

```text
artifacts/stress/afterblock_demo_proof_manifest.json
artifacts/stress/paper_plugin_local_load_test.json
```
