#!/usr/bin/env python3
"""Emit a compact proof manifest for the AfterBlock hackathon demo."""

from __future__ import annotations

import hashlib
import json
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_PATH = ROOT / "artifacts" / "stress" / "afterblock_demo_proof_manifest.json"


def sha1(path: Path) -> str:
    h = hashlib.sha1()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def zip_names(path: Path) -> list[str]:
    with zipfile.ZipFile(path) as zf:
        return zf.namelist()


def count_pack_assets(path: Path) -> dict[str, int]:
    with zipfile.ZipFile(path) as zf:
        names = zf.namelist()
        paper_model = json.loads(zf.read("assets/minecraft/models/item/paper.json").decode("utf-8"))
    return {
        "textures": sum(
            name.startswith("assets/minecraft/textures/item/afterblock/") and name.endswith(".png")
            for name in names
        ),
        "models": sum(
            name.startswith("assets/minecraft/models/item/afterblock/") and name.endswith(".json")
            for name in names
        ),
        "paper_overrides": len(paper_model.get("overrides", [])),
    }


def plugin_metadata(path: Path) -> dict[str, str]:
    with zipfile.ZipFile(path) as zf:
        plugin_yml = zf.read("plugin.yml").decode("utf-8")
    data: dict[str, str] = {}
    for line in plugin_yml.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            data[key.strip()] = value.strip()
    return data


def server_zip_checks(path: Path) -> dict:
    names = zip_names(path)
    required = [
        "plugins/DreamWall/config.yml",
        "plugins/dreamwall-paper-bridge-0.1.0.jar",
        "AfterBlockMuseum.zip",
        "afterblock-demo-world.zip",
        "afterblock-demo-proof.json",
        "afterblock-server-profile.json",
        "UPLOAD_TO_SERVER.md",
        "install-afterblock-paper.sh",
        "server.properties.append",
        "README.md",
    ]
    with zipfile.ZipFile(path) as zf:
        config = zf.read("plugins/DreamWall/config.yml").decode("utf-8")
        demo_proof = json.loads(zf.read("afterblock-demo-proof.json").decode("utf-8"))
        server_profile = json.loads(zf.read("afterblock-server-profile.json").decode("utf-8"))
        upload_guide = zf.read("UPLOAD_TO_SERVER.md").decode("utf-8")
        install_helper = zf.read("install-afterblock-paper.sh").decode("utf-8")
    return {
        "file": path.name,
        "required_files_present": {name: name in names for name in required},
        "config_contains": {
            "space_url": "space-url:" in config,
            "resource_pack_sha1": "resource-pack-sha1:" in config,
            "default_import_prompt": "default-import-prompt:" in config,
            "gallery_origin": "gallery-origin:" in config,
            "plot_size": "plot-size: 32" in config,
        },
        "demo_proof_contract": {
            "type": demo_proof.get("type") == "afterblock.paper-demo-proof.v1",
            "total_plots": demo_proof.get("coordinate_contract", {}).get("total_plots") == 144,
            "plot_scale": demo_proof.get("coordinate_contract", {}).get("plot_scale") == 32,
            "paper_overrides": demo_proof.get("resource_pack", {}).get("paper_overrides") == 3200,
            "import_command": "/dreamwall import" in demo_proof.get("expected_commands", []),
            "pebblehost_blocker": "PebbleHost" in demo_proof.get("blocked_external_step", ""),
        },
        "server_profile_contract": {
            "type": server_profile.get("type") == "afterblock.server-profile.v1",
            "space_url": bool(server_profile.get("space", {}).get("url")),
            "resource_pack_sha1": bool(server_profile.get("server", {}).get("resource_pack_sha1")),
            "default_import": all(
                server_profile.get("default_import", {}).get(key)
                for key in ["prompt", "story", "owner"]
            ),
            "upload_map": len(server_profile.get("upload_map", [])) >= 4,
            "museum_check": "/dreamwall museum check" in server_profile.get("verification_commands", []),
            "helper_files": set(server_profile.get("helper_files", []))
            >= {"UPLOAD_TO_SERVER.md", "install-afterblock-paper.sh"},
            "no_password": "password" not in json.dumps(server_profile).lower().replace("no password", ""),
        },
        "upload_helper_contract": {
            "script_has_sftp_env": "AFTERBLOCK_SFTP_HOST" in install_helper
            and "AFTERBLOCK_SFTP_USER" in install_helper,
            "script_runs_sftp": "sftp -P" in install_helper,
            "script_has_verify_commands": "/dreamwall museum check" in install_helper
            and "/dreamwall import here" in install_helper,
            "script_no_private_endpoint": not any(
                secret in install_helper.lower()
                for secret in ["password", "gmail", "itsarnav", "uk144"]
            ),
            "guide_has_upload_map": "Upload Map" in upload_guide
            and "plugins/DreamWall/config.yml" in upload_guide,
            "guide_has_minecraft_commands": "/dreamwall museum build" in upload_guide
            and "/dreamwall import here" in upload_guide,
        },
    }


def main() -> int:
    sys.path.insert(0, str(ROOT))
    import app  # noqa: WPS433 - imports the app's current constants and output contract.

    resource_pack = ROOT / app.RESOURCE_PACK_PATH
    plugin_jar = ROOT / app.PAPER_PLUGIN_JAR_PATH
    prebuilt_world = ROOT / app.PREBUILT_WORLD_PATH
    outputs = app.place_in_museum(
        app.DEFAULT_IMPORT_PROMPT,
        app.DEFAULT_IMPORT_STORY,
        app.DEFAULT_IMPORT_OWNER,
        None,
    )
    server_bundle = app.server_config_bundle()
    demo_path = app.demo_path_html()
    server_zip = Path(outputs[11])
    handoff = outputs[12]

    pack_counts = count_pack_assets(resource_pack)
    proof = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "goal": "AfterBlock Hugging Face Space configures a Paper server handoff for an exact-coordinate Minecraft memory museum.",
        "space_url": app.PUBLIC_SPACE_URL,
        "coordinate_contract": {
            "canvas_size": app.CANVAS_SIZE,
            "plot_scale": app.PLOT_SCALE,
            "origin": {
                "x": app.GALLERY_ORIGIN_X,
                "y": app.GALLERY_ORIGIN_Y,
                "z": app.GALLERY_ORIGIN_Z,
            },
            "formula": "world_x = -192 + plot_x * 32; world_y = 80; world_z = -192 + plot_z * 32",
            "total_plots": app.CANVAS_SIZE * app.CANVAS_SIZE,
        },
        "main_flow_contract": {
            "place_in_museum_outputs": len(outputs),
            "has_live_paper_handoff": "Live Paper handoff" in handoff,
            "has_import_command_copy": "/dreamwall import" in handoff,
            "has_xyz_and_cmd": "XYZ" in handoff and "CMD" in handoff,
            "server_zip_output_index": 11,
            "handoff_output_index": 12,
        },
        "server_config_ui_contract": {
            "bundle_outputs": len(server_bundle),
            "has_install_card": "Server owner install card" in server_bundle[2],
            "has_upload_map": "Upload map" in server_bundle[2],
            "has_verify_commands": "/dreamwall museum check" in server_bundle[2]
            and "/dreamwall import here" in server_bundle[2],
            "mentions_profile_json": "afterblock-server-profile.json" in server_bundle[2],
            "mentions_upload_helper": "UPLOAD_TO_SERVER.md" in server_bundle[2]
            and "install-afterblock-paper.sh" in server_bundle[2],
        },
        "demo_path_contract": {
            "has_judge_scorecard": "judge-scorecard" in demo_path,
            "has_winning_signal": "Winning signal" in demo_path,
            "cuts_feature_buffet": "Do not demo a feature buffet" in demo_path,
            "has_route_proof": "/dreamwall museum check" in demo_path
            and "route compass" in demo_path,
            "has_space_to_server_contract": "Space-to-server contract" in demo_path,
        },
        "resource_pack": {
            "path": app.RESOURCE_PACK_PATH,
            "sha1": sha1(resource_pack),
            "sha256": sha256(resource_pack),
            "expected_sha1_constant": app.RESOURCE_PACK_SHA1,
            "assets": pack_counts,
            "valid": (
                pack_counts["textures"] == 3200
                and pack_counts["models"] == 3200
                and pack_counts["paper_overrides"] == 3200
            ),
        },
        "paper_plugin": {
            "path": app.PAPER_PLUGIN_JAR_PATH,
            "sha1": sha1(plugin_jar),
            "sha256": sha256(plugin_jar),
            "expected_sha1_constant": app.PAPER_PLUGIN_SHA1,
            "expected_sha256_constant": app.PAPER_PLUGIN_SHA256,
            "plugin_yml": plugin_metadata(plugin_jar),
        },
        "prebuilt_world": {
            "path": app.PREBUILT_WORLD_PATH,
            "sha1": sha1(prebuilt_world),
            "sha256": sha256(prebuilt_world),
            "expected_sha1_constant": app.PREBUILT_WORLD_SHA1,
            "expected_sha256_constant": app.PREBUILT_WORLD_SHA256,
            "zip_entries": {
                "world_folder": any(name.startswith("world/") for name in zip_names(prebuilt_world)),
                "world_nether_folder": any(name.startswith("world_nether/") for name in zip_names(prebuilt_world)),
                "world_the_end_folder": any(name.startswith("world_the_end/") for name in zip_names(prebuilt_world)),
                "server_properties_absent": "server.properties" not in zip_names(prebuilt_world),
                "session_lock_absent": not any(name.endswith("session.lock") for name in zip_names(prebuilt_world)),
            },
        },
        "per_relic_server_zip": server_zip_checks(server_zip),
        "blocked_external_step": {
            "pebblehost_upload": "requires PebbleHost panel/SFTP password entered outside the repo",
            "sftp_endpoint_known": "sftp://uk144.pebblehost.net:2222",
        },
    }

    proof["passed"] = all(
        [
            proof["main_flow_contract"]["place_in_museum_outputs"] == 13,
            proof["main_flow_contract"]["has_live_paper_handoff"],
            proof["main_flow_contract"]["has_import_command_copy"],
            proof["main_flow_contract"]["has_xyz_and_cmd"],
            proof["server_config_ui_contract"]["bundle_outputs"] == 3,
            proof["server_config_ui_contract"]["has_install_card"],
            proof["server_config_ui_contract"]["has_upload_map"],
            proof["server_config_ui_contract"]["has_verify_commands"],
            proof["server_config_ui_contract"]["mentions_profile_json"],
            proof["server_config_ui_contract"]["mentions_upload_helper"],
            proof["demo_path_contract"]["has_judge_scorecard"],
            proof["demo_path_contract"]["has_winning_signal"],
            proof["demo_path_contract"]["cuts_feature_buffet"],
            proof["demo_path_contract"]["has_route_proof"],
            proof["demo_path_contract"]["has_space_to_server_contract"],
            proof["resource_pack"]["valid"],
            proof["resource_pack"]["sha1"] == proof["resource_pack"]["expected_sha1_constant"],
            proof["paper_plugin"]["sha1"] == proof["paper_plugin"]["expected_sha1_constant"],
            proof["paper_plugin"]["sha256"] == proof["paper_plugin"]["expected_sha256_constant"],
            proof["prebuilt_world"]["sha1"] == proof["prebuilt_world"]["expected_sha1_constant"],
            proof["prebuilt_world"]["sha256"] == proof["prebuilt_world"]["expected_sha256_constant"],
            all(proof["prebuilt_world"]["zip_entries"].values()),
            all(proof["per_relic_server_zip"]["required_files_present"].values()),
            all(proof["per_relic_server_zip"]["config_contains"].values()),
            all(proof["per_relic_server_zip"]["demo_proof_contract"].values()),
            all(proof["per_relic_server_zip"]["server_profile_contract"].values()),
            all(proof["per_relic_server_zip"]["upload_helper_contract"].values()),
        ]
    )

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(proof, indent=2) + "\n")
    print(json.dumps({"passed": proof["passed"], "proof": str(OUT_PATH)}, indent=2))
    return 0 if proof["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
