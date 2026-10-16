"""Shared fixtures. Registries are built once per session because they take seconds.

Tests run the live API on a small demonstration registry (tier XS) to keep the fast check
fast; the published demonstration uses tier S.
"""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("PYTHONUTF8", "1")
os.environ.setdefault("HAWIYYA_DEMO_TIER", "XS")


@pytest.fixture(scope="session")
def reg_s():  # type: ignore[no-untyped-def]
    from hawiyya.registry.build import build_registry

    return build_registry(3, "S")


@pytest.fixture(scope="session")
def ctx_s(reg_s):  # type: ignore[no-untyped-def]
    from hawiyya.normalise.record import normalise_registry

    return normalise_registry(reg_s.records)


@pytest.fixture(scope="session")
def reg_xs():  # type: ignore[no-untyped-def]
    from hawiyya.registry.build import build_registry

    return build_registry(5, "XS")


@pytest.fixture(scope="session")
def ctx_xs(reg_xs):  # type: ignore[no-untyped-def]
    from hawiyya.normalise.record import normalise_registry

    return normalise_registry(reg_xs.records)
