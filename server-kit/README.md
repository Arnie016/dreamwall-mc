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
`afterblock-demo-world.zip` is optional; unzip it into a clean server root if you want the already-built memory-spine museum world instead of running `/dreamwall museum build` live.

Current plugin jar checksums:

```text
sha1   6e005510f429cfb77aeffa00bee9d458dd0b0568
sha256 35aeae59268cef96c50f7757451455db5cce30804aa1bd4738532d4d5601762a
```

Current prebuilt world checksums:

```text
sha1   d5c5d80daf53f5e72bd8860aea884e221a1b9f84
sha256 33edcf48d00eca44e8076e5f62f5e3289c6686aecbf24e80349e9a6c2f7ed1f3
```
