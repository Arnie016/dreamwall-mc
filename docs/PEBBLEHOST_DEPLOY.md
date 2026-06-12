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
8854b0d78b4e2d252a2c3c8dd635c1dc20e06dd5f8323bd0b3a608c50bd089bf  AfterBlockMuseum.zip
d0634a5b6851c3e2aa8f09fa39461c2b7a5de1709623d2293147429a479a696c  dreamwall-paper-bridge-0.1.0.jar
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

Run `/dreamwall pack` in-game to ask the client to load that pack. Set `offer-resource-pack-on-join: true` in `plugins/DreamWall/config.yml` only if you want the server to offer it automatically when players join.

The pack contains:

```text
1,200 PNG item textures
1,200 item model JSON files
1,200 CustomModelData overrides on minecraft:paper
```

## In-Game Smoke Test

After restarting the server, run these as an op player:

```text
/dreamwall
/dreamwall fetch
/dreamwall pack
/dreamwall demo
/dreamwall import here
```

Expected result:

- `/dreamwall fetch` reports the Hugging Face Space is reachable.
- `/dreamwall pack` asks the player to load `AfterBlockMuseum.zip`.
- `/dreamwall demo` places a small pedestal, sign, visible `ItemDisplay`, and gives a Paper item using `CustomModelData 730002`.
- `/dreamwall import here` calls the live `curate_artifact` endpoint, parses `dreamwall.museum.v1`, places a packet-derived pedestal/sign/`ItemDisplay` beside the player, and gives a Paper item using the packet's `custom_model_data`.

If the Paper item looks like ordinary paper, the plugin is working but the resource pack is not loaded.

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
