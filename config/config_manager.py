"""Centralised configuration loader."""

import yaml
import logging
from pathlib import Path

_CFG: dict = {}
_CONFIG_PATH = Path(__file__).parent / "settings.yaml"


def load() -> dict:
    global _CFG
    if _CFG:
        return _CFG
    with open(_CONFIG_PATH, "r") as f:
        _CFG = yaml.safe_load(f)
    return _CFG


def get(section: str, key: str, default=None):
    cfg = load()
    return cfg.get(section, {}).get(key, default)
