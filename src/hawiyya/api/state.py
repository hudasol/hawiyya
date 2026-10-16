"""Application state for live mode: the demonstration registry, index and model."""

from __future__ import annotations

import os
import threading
from dataclasses import dataclass
from typing import Any

from hawiyya.lab.train import load_model
from hawiyya.normalise.record import normalise_registry
from hawiyya.registry.build import Registry, build_registry
from hawiyya.scoring.scorer import Model
from hawiyya.workflow.check import RegistryIndex

DEMO_SEED = 7  # a development seed; the demonstration registry is not an evaluation result
DEMO_TIER = os.environ.get("HAWIYYA_DEMO_TIER", "S")  # tests use XS to stay fast


@dataclass
class AppState:
    registry: Registry
    index: RegistryIndex
    model: Model
    extras: dict[str, Any]


_lock = threading.Lock()
_state: dict[str, AppState] = {}


def build_state(seed: int = DEMO_SEED, tier: str = DEMO_TIER) -> AppState:
    reg = build_registry(seed, tier)
    ctx = normalise_registry(reg.records)
    index = RegistryIndex.build(ctx, reg.records)
    return AppState(reg, index, load_model(), {})


def get_state() -> AppState:
    with _lock:
        if "s" not in _state:
            _state["s"] = build_state()
        return _state["s"]


def is_ready() -> bool:
    return "s" in _state
