# DreamWall: AfterBlock Museum Competition Goal

## Goal

Win the Build Small Hackathon by making DreamWall feel like a new way to preserve memory: an emotional Minecraft museum where real objects, prompted paintings, animals, and personal symbols become placed artifacts with passports and tiny spirits.

## Submission Bet

AfterBlock Museum is not a chatbot and not a normal image generator. It is a Minecraft museum ritual:

- visitors scan a relic, memory, animal spirit, or prompted painting
- the curator assigns a hall and museum placement
- each artifact receives curation scores, resonance links, and a plaque
- a constrained spirit awakens and speaks from the artifact lore
- the app renders a 3D Minecraft artifact, prints a passport card, exposes a live Paper handoff, and emits `dreamwall.museum.v1`
- the Minecraft server becomes the proof surface: the same relic gets a route compass, lit floor path, engraved nameplate, lectern passport, and right-click profile button at its generated XYZ

## What To Avoid For V1

- Real-money payments
- Blockchain/NFT claims
- Complex ownership law
- Persistent public multiplayer economy before the demo works

Use **curation score**, **visitor echoes**, and **resonance** instead of auction language.

## Winning Demo

One continuous three-minute video:

1. Open the Hugging Face Space.
2. Type one ordinary object and one story caption, then click **Place in Museum**.
3. Show the main 3D relic, `CustomModelData`, `/give` command, and **Live Paper handoff** card.
4. Show **Download Paper server kit for this relic** so judges understand that each visitor can configure their own Paper server handoff from the Space.
5. Show the living museum map, **You are here** banner, and exact XYZ.
6. Open **Passport** for the QR/share link and route.
7. Open **Relic Profile** briefly as the artifact's history/lore page.
8. Open **Packet** and show `dreamwall.museum.v1`.
9. Switch to Minecraft, run `/dreamwall museum check`, then `/dreamwall import`.
10. Show the atlas target, hold the route compass, follow the lit floor from `YOU ARE HERE`, and show the placed item, engraved nameplate, lectern passport, and profile button at the generated plot.
11. End with: "AfterBlock turns the things people would throw away into places they can visit."

## Critique

What works:

- The browser app has a clean job: turn one object and one story into a museum packet.
- The Minecraft server is the moat. It makes the memory spatial, walkable, and persistent instead of just another generated image.
- The exact coordinate contract is easy for judges to understand: the Space says `plot x,z`; Minecraft proves that exact plot exists.
- The passport/profile layer makes the "spirit" useful: it becomes the artifact's history page, not a vague chatbot.

What does not work if over-emphasized:

- A giant texture browser is impressive but noisy; use it only as backup proof.
- "Spirit" as a standalone feature sounds redundant unless it is framed as the relic profile/history.
- Generic-looking previews weaken the emotional hook. In the video, pick one object that renders clearly and has a specific caption.
- PebbleHost setup is not the story. The story is Space -> route compass -> exact in-world relic.

Best way to win:

- Demo one memorable relic, not ten features.
- Spend most of the video on the continuity proof: same prompt, same passport, same `CustomModelData`, same XYZ, same in-world artifact.
- Show the proof manifest only if asked; use it as judge confidence, not as the emotional centerpiece.
- If PebbleHost access is ready, record the live server. If not, record the locally verified Paper world and be explicit that PebbleHost upload is password-gated.

## Target Prizes

- OpenAI Codex Track: public GitHub repo with Codex-authored commits.
- Adventure in Thousand Token Wood: strange, emotional, delightful, AI-load-bearing, and small enough to run without a giant model dependency.
- Off-Brand: Minecraft museum terminal rather than default chatbot UI.
- Tiny Titan: constrained local semantic curation is far below the 32B ceiling and can be swapped for a <=4B model without changing the packet.
- Best Demo: object to 3D model to hall to passport/profile to exact-coordinate Minecraft proof in under three minutes.
- Community Choice: passport cards and optional social tags make the output shareable without forcing spam.
- Sharing is Caring: sample artifact traces and server packets make the system inspectable.
- Field Notes: `docs/FIELD_NOTES.md` explains why a Minecraft museum is a small-model memory machine.
- Judges' Wildcard: the weird coherent claim is that ordinary objects become places when the museum decides "when" they are art.
