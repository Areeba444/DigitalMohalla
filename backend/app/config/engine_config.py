"""Loader for the versioned assurance-engine configuration (NFR-D-01).

The file is the design baseline in docs/design/11_assurance_engine
(Assurance_Engine_Config_Draft.json), copied to backend/config/engine.json. Every stored
assessment records `config_version`, so changing any parameter means changing the file and bumping
that version. Values are initial, unvalidated hypotheses (see the file's own status fields);
nothing is hardcoded in the engine.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULT_PATH = Path(__file__).resolve().parents[2] / "config" / "engine.json"


@dataclass(frozen=True)
class EngineConfig:
    config_version: str
    data: dict[str, Any]

    def section(self, name: str) -> dict[str, Any]:
        section: dict[str, Any] = self.data[name]
        return section


def load_engine_config(path: Path = DEFAULT_PATH) -> EngineConfig:
    data = json.loads(path.read_text(encoding="utf-8"))
    return EngineConfig(config_version=data["config_metadata"]["config_version"], data=data)
