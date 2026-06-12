# AfterBlock Texture Pack Strategy

## Current Asset Set

- 1,200 generated relic textures
- 1,200 generated 3D item model JSON files
- 1,200 `minecraft:paper` custom model data overrides
- 40 everyday object archetypes
- 4 contact-sheet screenshots
- browser gallery for the first 240 isometric previews

Open locally:

```text
assets/afterblock_textures/gallery/index.html
```

Screenshots:

```text
assets/afterblock_textures/gallery/contact_sheet_01.png
assets/afterblock_textures/gallery/contact_sheet_02.png
assets/afterblock_textures/gallery/contact_sheet_03.png
assets/afterblock_textures/gallery/contact_sheet_04.png
```

Resource pack skeleton:

```text
resource-pack/AfterBlockMuseum/
```

## Minecraft Rendering Strategy

Each museum relic maps to:

- a 64x64 item texture
- a 3D model JSON with blocky `elements`
- GUI/ground/fixed/first-person/third-person display transforms
- a `custom_model_data` ID on `minecraft:paper`
- a museum packet field under `minecraft.resource_pack_item`

This lets the server use one base item, `minecraft:paper`, while rendering thousands of different relics.

## Why 3D Models Matter

PNG-only items feel like flat stickers. AfterBlock uses model JSON shapes so different relic categories read differently:

- books and notebooks: thin rectangular slabs
- monitors: screen + stand geometry
- bags: box body + handle
- bottles: tall body + cap
- lamps: shade + stem + base
- controllers: wide body + grips
- keys: ring + shaft
- mugs: cup + handle

The textures carry color and symbolic detail; the model geometry carries silhouette.

## Scale Strategy

To reach thousands of objects without hand-drawing every file:

1. Classify object into an archetype.
2. Pick base geometry for the archetype.
3. Generate color palette from object/memory/image fingerprint.
4. Add deterministic variant marks.
5. Emit PNG + model JSON + manifest row.
6. Map `custom_model_data` into the Minecraft bridge packet.

The current generator does this deterministically, so an object can be recreated from prompt, owner, and artifact metadata.

## Next Upgrade

Use a real vision model for uploaded images:

```text
photo -> object class -> palette -> archetype geometry -> resource-pack item -> Minecraft pedestal
```

The app already accepts an optional relic image and stores an image fingerprint. The next step is replacing the local color fingerprint with a VLM classifier.
