"""Clustering of LINK decisions with conflict checks (union find written here).

A plain connected component is not accepted: if two records in a component carry strong
evidence against each other (a contradicted pair), the component is rebuilt greedily from its
strongest LINK edges, refusing any edge that would join a contradicted pair. Every refused
edge goes to REVIEW with CLUSTER_CONFLICT, so no contradicted pair is merged silently.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass, field

CONTRADICTION_LOG_ODDS = -4.0  # ASSUMPTION: a scored pair this far below zero contradicts


class UnionFind:
    def __init__(self) -> None:
        self.parent: dict[str, str] = {}

    def find(self, x: str) -> str:
        self.parent.setdefault(x, x)
        root = x
        while self.parent[root] != root:
            root = self.parent[root]
        while self.parent[x] != root:  # path compression
            self.parent[x], x = root, self.parent[x]
        return root

    def union(self, a: str, b: str) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            if ra < rb:
                self.parent[rb] = ra
            else:
                self.parent[ra] = rb


@dataclass
class ClusterResult:
    clusters: list[list[str]]  # accepted clusters of two or more records, sorted
    accepted_edges: list[tuple[str, str, float]]
    conflict_edges: list[tuple[str, str, float]]  # LINK edges sent to REVIEW
    members_with_conflict: set[str] = field(default_factory=set)


def cluster(links: Iterable[tuple[str, str, float]],
            contradictions: Iterable[tuple[str, str]]) -> ClusterResult:
    """``links`` are LINK edges (a, b, probability); ``contradictions`` are pairs that must
    never end in one cluster."""
    links = sorted(((min(a, b), max(a, b), p) for a, b, p in links), key=lambda e: (-e[2], e[0], e[1]))
    against: dict[str, set[str]] = defaultdict(set)
    for a, b in contradictions:
        against[a].add(b)
        against[b].add(a)
    uf = UnionFind()
    members: dict[str, set[str]] = {}
    accepted: list[tuple[str, str, float]] = []
    conflicts: list[tuple[str, str, float]] = []
    for a, b, p in links:
        ra, rb = uf.find(a), uf.find(b)
        if ra == rb:
            accepted.append((a, b, p))
            continue
        ma = members.get(ra, {a})
        mb = members.get(rb, {b})
        if any(against[x] & mb for x in ma):
            conflicts.append((a, b, p))
            continue
        uf.union(a, b)
        root = uf.find(a)
        members[root] = ma | mb
        members.pop(ra if ra != root else rb, None)
        accepted.append((a, b, p))
    groups: dict[str, list[str]] = defaultdict(list)
    for x in uf.parent:
        groups[uf.find(x)].append(x)
    clusters = sorted(sorted(g) for g in groups.values() if len(g) > 1)
    flagged = {x for a, b, _ in conflicts for x in (a, b)}
    return ClusterResult(clusters, accepted, conflicts, flagged)
