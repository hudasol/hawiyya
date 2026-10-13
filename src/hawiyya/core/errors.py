"""Error types shared by every layer."""

from __future__ import annotations


class HawiyyaError(Exception):
    """Base class for all Hawiyya errors."""


class SchemaDriftError(HawiyyaError):
    """An input file does not have the columns or types the adapter expects."""


class ContractError(HawiyyaError):
    """A value violates the L0 contract."""


class SealedSeedError(HawiyyaError):
    """Code other than the sealed evaluation tried to touch a sealed seed."""


class InputBoundsError(HawiyyaError):
    """An input exceeds a documented bound (length, count or size)."""
