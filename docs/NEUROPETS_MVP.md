# NeuroPets MVP

NeuroPets is the mini version for the hackathon demo.

## Player Process

1. Player opens the Hugging Face Space.
2. Player enters creator name.
3. Player writes a creature seed prompt.
4. The app normalizes the prompt into a creature genome.
5. The app returns:
   - portrait
   - species card
   - traits
   - survival odds
   - current activity
   - cooldown
   - lineage
   - Minecraft spawn packet

## Prompt Rules

Players do not need to write a perfect creature prompt.

If they write:

```text
a leaf dropping from the sky
```

The system interprets it as:

```text
a soft airborne leaf-creature adapted to sky forest or mushroom swamp
```

If they write:

```text
an invincible god dragon
```

The system does **not** make it overpowered. Power words become aura/personality. Stats stay capped.

## Anti-Spam / Cooldown

V1 uses a generated cooldown field.

Recommended live rule:

- one active creature per creator name
- 45-120 second hatch cooldown
- additional prompts become mutations, not unlimited new pets
- repeated spam lowers survival/rarity

## Survival

Each creature has:

- habitat
- traits
- stats
- survival odds
- battle score
- generation
- current state

The server can run ecosystem ticks later:

```text
forage -> encounter -> battle/flee/fuse -> mutate -> update leaderboard
```

## Minecraft Server MVP

First PebbleHost demo:

1. Flat world.
2. Spawn area.
3. Creature preserve zones.
4. Leaderboard wall.
5. Lineage wall.
6. Signs or name tags for generated creatures.

The Space remains the hatchery. Minecraft is the living proof surface.
