"""
EngineSnapshot — Versioning and traceability for every engine run.

Every pipeline execution produces a snapshot that records:
- Which version of each layer was used
- Config hash at runtime
- Timestamp of execution
- Input parameters

This enables:
- Calibration debugging (what config produced this output?)
- Regression detection (did a layer version change cause drift?)
- Audit trail (when was this decision produced, with what inputs?)
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import hashlib


# Semantic version for each layer — bump when logic changes
ASTRONOMY_VERSION = "1.0.0"
FEATURE_VERSION = "1.0.0"
RULE_VERSION = "1.0.0"
DECISION_VERSION = "1.0.0"
ENGINE_VERSION = "2.0.0"  # overall engine version


@dataclass(frozen=True)
class EngineSnapshot:
    """
    Immutable record of engine state at execution time.

    Attached to every pipeline run output for full traceability.
    """
    # Layer versions
    engine_version: str = ENGINE_VERSION
    astronomy_version: str = ASTRONOMY_VERSION
    feature_version: str = FEATURE_VERSION
    rule_version: str = RULE_VERSION
    decision_version: str = DECISION_VERSION

    # Runtime metadata
    timestamp: str = ""                     # ISO 8601 when the run executed
    config_hash: str = ""                   # SHA-256 of config used (first 16 chars)
    ayanamsa: str = "FAGAN_BRADLEY"

    # Input trace
    eval_date: str = ""                     # ISO 8601 of evaluation date
    birth_date: str = ""                    # ISO 8601 of birth date
    location_lat: float = 0.0
    location_lon: float = 0.0
    mode: str = "C"                         # A / B / C

    # Pipeline execution trace
    pipeline_stages_completed: int = 0      # 0-4 (how far the pipeline ran)


def create_snapshot(
    eval_date: datetime,
    birth_data: dict,
    mode: str = "C",
    config: Optional[dict] = None,
    lat: float = 0.0,
    lon: float = 0.0,
    stages_completed: int = 4,
) -> EngineSnapshot:
    """
    Create a snapshot for the current engine run.

    Args:
        eval_date: evaluation datetime
        birth_data: dict with 'date', 'lat', 'lon'
        mode: engine mode (A/B/C)
        config: optional config dict (for hashing)
        lat: resolved latitude
        lon: resolved longitude
        stages_completed: number of pipeline stages that ran (0-4)

    Returns:
        EngineSnapshot (frozen)
    """
    # Hash the config for traceability
    config_str = str(sorted(config.items())) if config else ""
    config_hash = hashlib.sha256(config_str.encode()).hexdigest()[:16] if config_str else "no_config"

    return EngineSnapshot(
        engine_version=ENGINE_VERSION,
        astronomy_version=ASTRONOMY_VERSION,
        feature_version=FEATURE_VERSION,
        rule_version=RULE_VERSION,
        decision_version=DECISION_VERSION,
        timestamp=datetime.utcnow().isoformat() + "Z",
        config_hash=f"sha256:{config_hash}",
        ayanamsa="FAGAN_BRADLEY",
        eval_date=eval_date.isoformat(),
        birth_date=birth_data["date"].isoformat() if birth_data else "",
        location_lat=lat,
        location_lon=lon,
        mode=mode,
        pipeline_stages_completed=stages_completed,
    )
