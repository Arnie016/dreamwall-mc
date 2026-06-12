import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import DEMO_ARTIFACTS, build_museum_artifact, museum_packet_for


GENERATED_VARIANTS = [
    {
        "owner_name": "Mira",
        "owner_handle": "@pixelmira",
        "input_type": "object_photo",
        "source_prompt": "a scratched blue water bottle with a moon sticker",
        "memory_text": "It sat beside every late-night build and made the desk feel survivable.",
    },
    {
        "owner_name": "Jon",
        "owner_handle": "@lampkeeper",
        "input_type": "object_photo",
        "source_prompt": "a warm desk lamp beside messy notes",
        "memory_text": "It kept one square of the room awake when the rest of the house was asleep.",
    },
    {
        "owner_name": "Nova",
        "owner_handle": "@bookishnova",
        "input_type": "memory_prompt",
        "source_prompt": "a toy car from a childhood shelf",
        "memory_text": "It was speed before distance became real.",
    },
    {
        "owner_name": "Ivy",
        "owner_handle": "@redstoneivy",
        "input_type": "animal_spirit",
        "source_prompt": "a fox that represents curiosity",
        "memory_text": "It appears whenever a locked room feels more like an invitation.",
    },
    {
        "owner_name": "Kai",
        "owner_handle": "@skyreceipt",
        "input_type": "painting_prompt",
        "source_prompt": "a cloud dragon sleeping inside a circuit board",
        "memory_text": "A strange painting about softness hiding inside machines.",
    },
]


def trace_for(seed_name: str, config: dict) -> dict:
    artifact = build_museum_artifact(**config)
    packet = museum_packet_for(artifact)
    top_scores = sorted(
        artifact["curation_scores"].items(),
        key=lambda item: item[1] if isinstance(item[1], int) else -1,
        reverse=True,
    )[:3]
    return {
        "seed_name": seed_name,
        "input": {
            "owner_handle": config["owner_handle"],
            "input_type": config["input_type"],
            "source_prompt": config["source_prompt"],
            "memory_text": config["memory_text"],
        },
        "curation_interpretation": {
            "object_guess": artifact["object_guess"],
            "hall": artifact["hall"],
            "zone": artifact["zone"],
            "placement_reason": artifact["placement_reason"],
            "top_scores": top_scores,
            "curation_score": artifact["curation_scores"]["curation_score"],
        },
        "spirit_output": {
            "name": artifact["spirit_name"],
            "traits": artifact["spirit_traits"],
            "first_line": artifact["spirit_first_line"],
            "sample_questions": artifact["sample_visitor_questions"],
            "sample_replies": artifact["sample_spirit_responses"],
        },
        "passport_fields": artifact["passport_card"],
        "minecraft_packet": packet["minecraft"],
        "museum_packet": packet,
    }


def main() -> None:
    traces = []
    for name, config in DEMO_ARTIFACTS.items():
        traces.append(trace_for(name, config))
    for index, config in enumerate(GENERATED_VARIANTS, 1):
        traces.append(trace_for(f"generated_variant_{index}", config))

    out = Path("data/artifact_traces.jsonl")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(json.dumps(trace, sort_keys=True) for trace in traces) + "\n", encoding="utf-8")
    print(f"wrote {len(traces)} artifact traces to {out}")


if __name__ == "__main__":
    main()
