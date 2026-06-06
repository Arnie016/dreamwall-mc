# Field Notes: DreamWall MC

## What I Built

DreamWall MC is a tiny Minecraft art ritual. A player writes a sentence, signs it with their username, and chooses a gallery wall. The app turns that context into a Minecraft painting preview, a block palette, WorldEdit row runs, and a trace of the model interpretation.

## Why It Fits Build Small

The project is not trying to use a giant model as a generic assistant. It uses a tiny local semantic fingerprint engine to make language feel physical in a Minecraft world. The prompt and player profile are load-bearing because they change the generated palette, symmetry, motifs, and wall instructions.

## What Makes It Strange

Two players can type the same sentence and get different paintings because the player name and gallery zone are part of the creative fingerprint. Changing one word can move the painting from cozy to cursed, or from mossy to mechanical.

## Next Server Step

The next layer is a Paper plugin for a live Minecraft server. The repo now includes a bridge scaffold in `paper-plugin/`. The plugin already knows where the Space lives and can test Hugging Face reachability with `/dreamwall fetch`.

The next implementation target is converting `grid.row_runs` from the Space packet into real block placement at a fixed gallery wall.

## Competition Bet

The project is designed to stand out by being a live shared world, not a static generator. The strongest demo is one continuous shot:

1. Type a prompt in the Space.
2. Show the generated Minecraft bridge packet.
3. Run the bridge on a Paper server.
4. Walk up to the DreamWall and see the new painting appear.
