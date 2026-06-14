# AfterBlock Demo Runbook

## Story

AfterBlock Museum preserves ordinary objects as Minecraft artifacts. The Space acts like a museum terminal: it scans a relic, assigns a hall, awakens a tiny spirit, prints a passport card, and emits a bridge packet for the server.

## Script

1. Show the Hugging Face Space.
2. Type one prompt in **Museum prompt**, for example: "my scratched blue water bottle from school with a moon sticker."
3. Click **Place in Museum**.
4. Show the live 3D relic, `CustomModelData`, `/give` command, and **Live Paper handoff** card in the main output.
5. Show **Download Paper server kit for this relic** so judges see the Space can configure the server handoff.
6. Show the living museum map and the "You are here" banner.
7. Open **Passport** and show the QR/share link plus exact Minecraft coordinates.
8. Open **Relic Profile** briefly as the artifact's history/lore page.
9. Open **Packet** and show `dreamwall.museum.v1`.
10. Switch to Minecraft and run `/dreamwall museum check`, then `/dreamwall import`.
11. Hold the route compass, follow the lit floor from `YOU ARE HERE`, and show the resource-pack item, engraved nameplate, profile button, and lectern passport at the packet coordinates.
12. End with: "AfterBlock turns the things people would throw away into places they can visit."

## Video Requirements

- Keep the final demo under three minutes.
- Show both the Space and Minecraft world.
- Do not explain implementation details in the voiceover.
- Focus on the magic: a memory becomes a 3D Minecraft artifact, a place, and a spirit.
- Use the **Demo Path** tab in the Space as the live shot checklist.
- Run `.venv/bin/python tools/verify_afterblock_demo.py` before recording if you need a proof packet for judges.

## Submission Checklist

- Hugging Face Space is running.
- GitHub repo link is in Space README.
- GitHub commits are Codex-authored.
- Field notes are present.
- Demo video shows real UI and Minecraft proof.
- Social post says this is a Minecraft memory museum, not a chatbot.
