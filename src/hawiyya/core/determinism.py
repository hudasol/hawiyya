"""Determinism helpers: seeded generators and canonical hashing.

Every stochastic step in Hawiyya takes an explicit seed. Hashes are computed over a
canonical JSON form so the same inputs give the same hash on every platform.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

import numpy as np


def rng(seed: int, *stream: str | int) -> np.random.Generator:
    """Return a numpy generator for ``seed`` and an optional named sub stream.

    Sub streams let independent parts of a pipeline draw numbers without changing
    each other's sequences when one part changes how many numbers it consumes.
    """
    material = [int(seed)] + [_stream_int(s) for s in stream]
    return np.random.default_rng(np.random.SeedSequence(material))


def _stream_int(part: str | int) -> int:
    if isinstance(part, int):
        return part
    return int.from_bytes(hashlib.sha256(part.encode("utf-8")).digest()[:8], "big")


def canonical_json(obj: Any) -> str:
    """Serialise ``obj`` to a canonical JSON string (sorted keys, no spaces, UTF-8)."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)


def stable_hash(obj: Any, length: int = 16) -> str:
    """Return a short hexadecimal SHA 256 digest of the canonical JSON form of ``obj``."""
    digest = hashlib.sha256(canonical_json(obj).encode("utf-8")).hexdigest()
    return digest[:length]


def sha256_file(path: str) -> str:
    """Return the full SHA 256 of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()
