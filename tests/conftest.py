"""Shared fixtures. Registries are built once per session because they take seconds."""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("PYTHONUTF8", "1")


@pytest.fixture(scope="session")
def reg_s():  # type: ignore[no-untyped-def]
    from hawiyya.registry.build import build_registry

    return build_registry(3, "S")


@pytest.fixture(scope="session")
def reg_xs():  # type: ignore[no-untyped-def]
    from hawiyya.registry.build import build_registry

    return build_registry(5, "XS")
