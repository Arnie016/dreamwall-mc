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
dist/pebblehost/SHA256SUMS
```

Current hashes from the verified local bundle:

```text
e6b53404d28a26732f0d28398d81b47e465045e7e4286039c6346c2d302a4148  AfterBlockMuseum.zip
061bdb4d23318826b660fb4845125e1713de2040841038019721ebc66e3c509c  dreamwall-paper-bridge-0.1.0.jar
```

## Upload Targets

Upload with SFTP or the PebbleHost file manager:

```text
plugins/dreamwall-paper-bridge-0.1.0.jar
AfterBlockMuseum.zip
```

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
/dreamwall demo
/dreamwall import here
```

Expected result:

- `/dreamwall fetch` reports the Hugging Face Space is reachable.
- `/dreamwall pack` asks the player to load `AfterBlockMuseum.zip`.
- `/dreamwall museum where` prints the exact Space-to-world coordinate formula.
- `/dreamwall museum build` creates the 12 x 12 AfterBlock campus: plot pads, hall gates, banner markers, entrance signage, and a `YOU ARE HERE` beacon.
- `/dreamwall demo` places a small pedestal, sign, visible `ItemDisplay`, and gives a Paper item using `CustomModelData 730002`.
- `/dreamwall import here` calls the live `curate_artifact` endpoint, parses `dreamwall.museum.v1`, places a packet-derived pedestal/sign/`ItemDisplay` beside the player, and gives a Paper item using the packet's `custom_model_data`.
- `/dreamwall import` places the packet-derived artifact at the generated museum coordinates. The coordinate contract is `x = -192 + plot_x * 32`, `y = 80`, `z = -192 + plot_z * 32`.

If the Paper item looks like ordinary paper, the plugin is working but the resource pack is not loaded.

For the three-minute video, the best proof order is:

1. Create a relic in the Space and show the passport/packet coordinate.
2. Join the Paper server and run `/dreamwall museum build`.
3. Run `/dreamwall import` so the same relic appears at the exact generated plot.
4. Walk from the `YOU ARE HERE` beacon to the plot pad and show the resource-pack item.

## Local Proof

Codex verified the plugin boots on Paper before PebbleHost install:

```text
Paper 1.21.4 build 232
Java Temurin 21.0.11
DreamWall enabled
dreamwall fetch reached the Hugging Face Space
dreamwall pack printed the public pack URL and SHA1
```

Proof file:

```text
artifacts/stress/paper_plugin_local_load_test.json
```
