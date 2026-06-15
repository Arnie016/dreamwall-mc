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
`afterblock-demo-world.zip` is optional; unzip it into a clean server root if you want the already-built memory-spine museum base with the 144 plot pads, `YOU ARE HERE` beacon, and living entry atlas already verified. Run `/dreamwall museum build` later only if you want to refresh the campus.

Current plugin jar checksums:

```text
sha1   93c09d2182737b5f7998ebca259e82dbfa2b71c1
sha256 8046f39b9d53ef2421e6e36b635d7f8b922e3c5759e59adfe044670e1149f0dc
```

Current prebuilt world checksums:

```text
sha1   c438d7dcb98493f436e0ca32aa6c8f73035fbdc0
sha256 e4634fb17b6aefcb1f075701727cb3c34bb94ce1886dcbb6c729dc0cb4515a6a
```
