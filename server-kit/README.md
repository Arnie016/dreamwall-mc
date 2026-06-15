# AfterBlock Paper Server Kit

This folder contains the Paper bridge jar served by the Hugging Face Space.

Use it with the Space-generated `plugins/DreamWall/config.yml`, then run:

```text
/dreamwall pack
/dreamwall museum build
/dreamwall museum check
/dreamwall import
```

The generated config controls the default prompt, story, and visitor signature used by `/dreamwall import`.
`/dreamwall museum build` creates the coordinate-accurate campus plus a physical 12x12 entry atlas that `/dreamwall import` marks when the live relic lands.
`afterblock-demo-world.zip` is optional; unzip it into a clean server root if you want the already-built memory-spine museum base. Run `/dreamwall museum build` once after restart to refresh the latest entry atlas.

Current plugin jar checksums:

```text
sha1   93c09d2182737b5f7998ebca259e82dbfa2b71c1
sha256 8046f39b9d53ef2421e6e36b635d7f8b922e3c5759e59adfe044670e1149f0dc
```

Current prebuilt world checksums:

```text
sha1   d5c5d80daf53f5e72bd8860aea884e221a1b9f84
sha256 33edcf48d00eca44e8076e5f62f5e3289c6686aecbf24e80349e9a6c2f7ed1f3
```
