"""Repository and safety-contract checks."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
INTEGRATION = ROOT / "custom_components" / "pentek_intellidrive"


def test_metadata() -> None:
    manifest = json.loads((INTEGRATION / "manifest.json").read_text(encoding="utf-8"))
    hacs = json.loads((ROOT / "hacs.json").read_text(encoding="utf-8"))
    assert manifest["domain"] == "pentek_intellidrive"
    assert manifest["config_flow"] is True
    assert manifest["version"] == "0.1.0"
    assert hacs["homeassistant"] == "2026.10.2"


def test_english_translation_matches_source_strings() -> None:
    strings = json.loads((INTEGRATION / "strings.json").read_text(encoding="utf-8"))
    english = json.loads(
        (INTEGRATION / "translations" / "en.json").read_text(encoding="utf-8")
    )
    assert english == strings


def test_v01_has_no_write_surface() -> None:
    component_files = list(INTEGRATION.glob("*.py"))
    source = "\n".join(path.read_text(encoding="utf-8") for path in component_files)
    assert "write_register" not in source
    assert "async_register_entity_service" not in source
    assert not (INTEGRATION / "number.py").exists()
    assert not (INTEGRATION / "switch.py").exists()
    assert not (INTEGRATION / "services.yaml").exists()
