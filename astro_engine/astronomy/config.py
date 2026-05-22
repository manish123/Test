"""
Versioned Configuration System (Req 60)

Loads all numeric thresholds, multipliers, caps, and bonuses from a versioned
YAML config file. No threshold is hardcoded in module logic — all are looked up
from the loaded config.
"""

import os
import hashlib
import yaml

_CONFIG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "configs")
_DEFAULT_CONFIG = "v2.0.0.yaml"

_loaded_config = None
_config_version = None
_config_hash = None


class ConfigValidationError(Exception):
    """Raised when a required config key is missing or invalid."""
    pass


REQUIRED_TOP_KEYS = [
    "version",
    "released",
    "planet_state",
    "event_scoring",
    "reference_weights",
    "multipliers",
    "mmt",
    "confidence",
    "risk",
    "decision",
    "node_anti_double_count",
    "sector_validation",
    "trading_gate",
]


def _validate_config(cfg):
    """Validate that all required top-level keys exist."""
    missing = [k for k in REQUIRED_TOP_KEYS if k not in cfg]
    if missing:
        raise ConfigValidationError(f"Missing required config keys: {missing}")

    if "dignity_multipliers" not in cfg.get("planet_state", {}):
        raise ConfigValidationError("Missing planet_state.dignity_multipliers")
    if "house_bonus" not in cfg.get("event_scoring", {}):
        raise ConfigValidationError("Missing event_scoring.house_bonus")


def load_config(config_path=None):
    """Load and validate a config file. Caches the result."""
    global _loaded_config, _config_version, _config_hash

    if config_path is None:
        config_path = os.path.join(_CONFIG_DIR, _DEFAULT_CONFIG)

    if not os.path.exists(config_path):
        raise ConfigValidationError(f"Config file not found: {config_path}")

    with open(config_path, "r") as f:
        raw = f.read()

    cfg = yaml.safe_load(raw)
    _validate_config(cfg)

    _config_hash = hashlib.sha256(raw.encode()).hexdigest()
    _config_version = cfg.get("version", "unknown")
    _loaded_config = cfg
    return cfg


def get_config():
    """Get the currently loaded config, loading default if needed."""
    global _loaded_config
    if _loaded_config is None:
        load_config()
    return _loaded_config


def get_config_meta():
    """Return version and hash for API response embedding."""
    if _loaded_config is None:
        load_config()
    return {
        "version": _config_version,
        "hash": f"sha256:{_config_hash[:16]}",
    }


def cfg(path, default=None):
    """
    Lookup a config value by dot-separated path.
    Example: cfg("event_scoring.house_bonus.tier_exalted_bonus") -> 35
    """
    config = get_config()
    keys = path.split(".")
    val = config
    for k in keys:
        if isinstance(val, dict):
            val = val.get(k)
        else:
            return default
        if val is None:
            return default
    return val


def compare_configs(path_a, path_b):
    """Compare two config files and report differences."""
    with open(path_a) as f:
        cfg_a = yaml.safe_load(f.read())
    with open(path_b) as f:
        cfg_b = yaml.safe_load(f.read())

    diffs = []
    _compare_recursive(cfg_a, cfg_b, "", diffs)
    return diffs


def _compare_recursive(a, b, prefix, diffs):
    if isinstance(a, dict) and isinstance(b, dict):
        all_keys = set(list(a.keys()) + list(b.keys()))
        for k in sorted(all_keys):
            path = f"{prefix}.{k}" if prefix else k
            if k not in a:
                diffs.append({"path": path, "old": None, "new": b[k], "delta": "added"})
            elif k not in b:
                diffs.append({"path": path, "old": a[k], "new": None, "delta": "removed"})
            else:
                _compare_recursive(a[k], b[k], path, diffs)
    elif a != b:
        delta = None
        if isinstance(a, (int, float)) and isinstance(b, (int, float)):
            delta = b - a
        diffs.append({"path": prefix, "old": a, "new": b, "delta": delta})
