# AfterBlock Demo Runbook

## Story

AfterBlock Museum preserves ordinary objects as Minecraft artifacts. The Space acts like a museum terminal: it scans a relic, assigns a hall, awakens a tiny spirit, prints a passport card, and emits a bridge packet for the server.

## Script

1. Show the Hugging Face Space.
2. Type one prompt in **Museum prompt**, for example: "my scratched blue water bottle from school with a moon sticker."
3. Click **Place in Museum**.
4. Show the live 3D relic and the collapsed **Minecraft proof and owner files** card only if you need the command.
5. Open **Placement** and show the living map, `YOU ARE HERE` banner, and lit route.
6. Open **Passport + Profile** and show the QR/share link plus the relic history.
7. Open **Join Minecraft** and show the server address plus the three player commands: `/dreamwall pack`, `/dreamwall museum check`, `/dreamwall import`.
8. Open **Object Atlas** only as backup proof if a judge asks how many object looks exist.
9. Open **Packet** only briefly if you need to prove the shared `dreamwall.museum.v1` packet.
10. Switch to Minecraft and run `/dreamwall pack`, `/dreamwall museum check`, then `/dreamwall import`.
11. Show the atlas target, hold the route compass, follow the lit floor from `YOU ARE HERE`, and show the resource-pack item, engraved nameplate, profile button, and lectern passport at the packet coordinates.
12. End with: "AfterBlock turns the things people would throw away into places they can visit."

## Video Requirements

- Keep the final demo under three minutes.
- Show both the Space and Minecraft world.
- Do not explain implementation details in the voiceover.
- Focus on the magic: a memory becomes a 3D Minecraft artifact, a place, and a spirit.
- Keep downloads/SFTP in the appendix unless a judge asks how to install it.
- Use the **Demo Path** tab in the Space as the live shot checklist.
- Run `.venv/bin/python tools/verify_afterblock_demo.py` before recording if you need a proof packet for judges.

## Submission Checklist

- Hugging Face Space is running.
- GitHub repo link is in Space README.
- GitHub commits are Codex-authored.
- Field notes are present.
- Demo video shows real UI and Minecraft proof.
- Social post says this is a Minecraft memory museum, not a chatbot.
