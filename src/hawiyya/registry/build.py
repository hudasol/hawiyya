"""Registry assembly: population source, identity layer and a generator (G1 or G2)."""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date
from functools import lru_cache
from typing import Any

import numpy as np

from hawiyya.contract.models import Record, TruthLabels
from hawiyya.core.determinism import canonical_json, rng, stable_hash
from hawiyya.core.paths import DATA
from hawiyya.core.sealed import check_seed
from hawiyya.registry.facilities import FACILITIES, Facility
from hawiyya.registry.g1.engine import G1Config, registration_date, render_record
from hawiyya.registry.lexicon import Lexicon, default_lexicon
from hawiyya.registry.people import People, Person, build_people
from hawiyya.registry.rendered import Rendered
from hawiyya.registry.source import PopulationPerson, native_population, read_sample
from hawiyya.registry.truth import TruthView
from hawiyya.registry.view import RegistrationView

TIERS = {"XS": 600, "S": 5000, "M": 20000, "L": 100000}
FACILITY_COUNT_P = (0.25, 0.35, 0.25, 0.15)  # ASSUMPTION: 1 to 4 facilities per person
SAME_FACILITY_REPEAT = 0.05  # ASSUMPTION: share of people registered twice at one facility

Renderer = Callable[[Person, People, Facility, date, np.random.Generator, str], Rendered]


@dataclass(frozen=True)
class Registry:
    view: RegistrationView
    truth: TruthView
    meta: dict[str, Any] = field(default_factory=dict)

    @property
    def records(self) -> tuple[Record, ...]:
        return self.view.records

    def digest(self) -> str:
        rows = [r.model_dump(mode="json") for r in self.view.records]
        labels = [self.truth.labels[r.record_id].model_dump(mode="json") for r in self.view.records]
        return stable_hash({"records": rows, "labels": labels}, length=64)


def data_source() -> str:
    manifest = DATA / "MANIFEST.json"
    if manifest.exists():
        return str(json.loads(manifest.read_text(encoding="utf-8"))["data_source"])
    return "native"


@lru_cache(maxsize=2)
def population_pool(source: str) -> tuple[PopulationPerson, ...]:
    if source == "synthea":
        return tuple(read_sample())
    return tuple(native_population(25000, seed=20261013))


def sample_population(n: int, seed: int, source: str) -> list[PopulationPerson]:
    pool = population_pool(source)
    if n > len(pool):
        raise ValueError(f"tier needs {n} persons; the {source} pool has {len(pool)}")
    idx = np.sort(rng(seed, "sample").choice(len(pool), size=n, replace=False))
    return [pool[int(i)] for i in idx]


def _g1_renderer(cfg: G1Config) -> Renderer:
    def render(p: Person, people: People, fac: Facility, reg: date,
               g: np.random.Generator, file_no: str) -> Rendered:
        return render_record(p, people, fac, reg, g, cfg, file_no)

    return render


def build_registry(seed: int, tier: str = "S", generator: str = "G1",
                   source: str | None = None, placeholder_share: float | None = None,
                   lexicon: Lexicon | None = None, n_persons: int | None = None) -> Registry:
    """Build a deterministic synthetic registry. Same arguments give an identical registry."""
    check_seed(seed)
    src = source or data_source()
    n = n_persons or TIERS[tier]
    lex = lexicon or default_lexicon()
    people = build_people(sample_population(n, seed, src), lex, seed)
    if generator == "G1":
        renderer = _g1_renderer(G1Config(placeholder_override=placeholder_share))
    elif generator == "G2":
        from hawiyya.registry.g2.engine import G2Config, g2_renderer

        renderer = g2_renderer(G2Config(placeholder_override=placeholder_share))
    else:
        raise ValueError(f"unknown generator {generator}")
    g = rng(seed, "registrations", generator)
    fac_w = np.array([f.weight for f in FACILITIES])
    pending: list[tuple[dict[str, object], TruthLabels]] = []
    file_counter = 0
    for p in people.persons:
        k = int(g.choice(4, p=np.array(FACILITY_COUNT_P))) + 1
        chosen = g.choice(len(FACILITIES), size=k, replace=False, p=fac_w / fac_w.sum())
        facs = [FACILITIES[int(i)] for i in chosen]
        if g.random() < SAME_FACILITY_REPEAT:
            facs.append(facs[0])
        dates = sorted(registration_date(p, g, first=(j == 0)) for j in range(len(facs)))
        for fac, reg in zip(facs, dates, strict=True):
            file_counter += 1
            file_no = f"{fac.facility_id}-{file_counter:06d}"
            out = renderer(p, people, fac, reg, g, file_no)
            label = TruthLabels(
                record_id="", person_id=p.person_id, family_id=p.family_id,
                twin_group=p.twin_group, origin_group=p.origin, facility_style=fac.style,
                name_style=out.name_style, corruption_log=list(out.log),
            )  # fmt: skip
            pending.append((out.fields, label))
    order = g.permutation(len(pending))
    records: list[Record] = []
    labels: dict[str, TruthLabels] = {}
    for new_idx, old_idx in enumerate(order):
        fields, label = pending[int(old_idx)]
        rid = f"R{new_idx:06d}"
        records.append(Record.model_validate({"record_id": rid, **fields}))
        labels[rid] = label.model_copy(update={"record_id": rid})
    meta = {
        "seed": seed, "tier": tier, "generator": generator, "data_source": src,
        "n_persons": n, "n_records": len(records), "lexicon_author": lex.author,
        "placeholder_share": placeholder_share,
    }  # fmt: skip
    return Registry(RegistrationView(tuple(records)), TruthView(labels, people), meta)


def registry_bytes(reg: Registry) -> bytes:
    """Canonical serialisation used by the determinism test."""
    rows = [r.model_dump(mode="json") for r in reg.records]
    return canonical_json(rows).encode("utf-8")
