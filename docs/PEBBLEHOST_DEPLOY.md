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
0bc7e6b3bb2e80b01943cea42bb3efdd7432eac6db39e394b3564dbfc584829e  dreamwall-paper-bridge-0.1.0.jar
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
/dreamwall demo
/dreamwall import here
```

Expected result:

- `/dreamwall fetch` reports the Hugging Face Space is reachable.
- `/dreamwall demo` places a small pedestal and gives a Paper item using `CustomModelData 730002`.
- `/dreamwall import here` calls the live `curate_artifact` endpoint, parses `dreamwall.museum.v1`, places a packet-derived pedestal/sign beside the player, and gives a Paper item using the packet's `custom_model_data`.

If the Paper item looks like ordinary paper, the plugin is working but the resource pack is not loaded.
