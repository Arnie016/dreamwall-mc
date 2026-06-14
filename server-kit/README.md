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
sha1   e6fb5eda3ebd84c15bb5ca9e0b2a2233942213c0
sha256 15869a7e7b4c1139b4340a9f90ffe77f079a6c69bd53176910030b79f9f15a83
```

Current prebuilt world checksums:

```text
sha1   d5c5d80daf53f5e72bd8860aea884e221a1b9f84
sha256 33edcf48d00eca44e8076e5f62f5e3289c6686aecbf24e80349e9a6c2f7ed1f3
```
