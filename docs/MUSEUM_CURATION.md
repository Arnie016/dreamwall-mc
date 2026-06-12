# Museum Curation

AfterBlock Museum should feel like memories have resonance, not like plots are being sold.

## Curation Signals

The app computes curation from:

- **Nostalgia:** childhood, firsts, school, home, and remembered routines.
- **Symbolism:** objects that carry myth, signal, protection, or identity.
- **Identity:** how strongly the relic belongs to the owner.
- **Companionship:** objects that stayed close through ordinary days.
- **Transformation:** exams, trades, moves, first years, and turning points.
- **Rarity:** unusual object/memory combinations.
- **Palette rarity:** rare Minecraft materials in the artifact palette.
- **Adjacency resonance:** nearby museum artifacts that echo the new relic.
- **Visitor echoes:** how likely visitors are to ask about it.

## Resonance

Resonance replaces auction language.

Examples:

- AirPods from first year of university resonate with Lost Signals and Soft Things.
- A childhood Star Wars book resonates with Worlds and Firsts.
- A monitor used for a first Bitcoin trade resonates with Tools and Turning Points.
- A school bag carried through exams resonates with Companions and pressure memories.

The key is emotional legibility: visitors should immediately understand why the artifact belongs in its hall.

## Why Not Market Language

Auction, reserve, and blockchain language distract from the stronger demo.

The winning V1 is:

```text
relic -> hall -> spirit -> passport -> Minecraft museum placement
```

The old `dreamwall.market.v1` packet can remain for compatibility, but the main user-facing packet is now `dreamwall.museum.v1`.
