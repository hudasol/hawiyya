"""Population sources: the Synthea adapter and the native generator.

Both produce the same schema (``PopulationPerson``), so switching source changes nothing
downstream. From Synthea only the synthetic patient id, birth date, sex, a coarse region
and the encounter count are kept. Synthea's names and identifiers are discarded and replaced
by the identity layer.
"""

from __future__ import annotations

import csv
import gzip
import io
from collections import Counter
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

import numpy as np

from hawiyya.core.determinism import rng
from hawiyya.core.errors import SchemaDriftError
from hawiyya.core.paths import DATA

SAMPLE_PATH = DATA / "samples" / "population.csv.gz"
SAMPLE_COLUMNS = ("person_id", "birth_date", "sex", "region", "encounters")
SYNTHEA_PATIENT_COLUMNS = ("Id", "BIRTHDATE", "DEATHDATE", "GENDER", "COUNTY")
SYNTHEA_ENCOUNTER_COLUMNS = ("PATIENT",)
REFERENCE_DATE = date(2026, 1, 1)


@dataclass(frozen=True)
class PopulationPerson:
    person_id: str
    birth_date: date
    sex: str  # "M" or "F"
    region: str
    encounters: int


def _require(header: Sequence[str] | None, needed: Iterable[str], file: Path) -> None:
    if header is None:
        raise SchemaDriftError(f"{file.name}: file is empty, expected columns {list(needed)}")
    for col in needed:
        if col not in header:
            raise SchemaDriftError(f"{file.name}: missing column {col!r}")


def read_synthea_chunks(base: Path) -> list[PopulationPerson]:
    """Read every ``chunkNN/csv/patients.csv`` (and encounters) under ``base``."""
    chunks = sorted(p for p in base.glob("chunk*/csv") if p.is_dir())
    if not chunks:
        raise SchemaDriftError(f"no Synthea chunk output under {base.name}")
    raw: list[tuple[str, str, str, str]] = []
    enc: Counter[str] = Counter()
    for csv_dir in chunks:
        pfile = csv_dir / "patients.csv"
        with pfile.open(encoding="utf-8", newline="") as fh:
            reader = csv.DictReader(fh)
            _require(reader.fieldnames, SYNTHEA_PATIENT_COLUMNS, pfile)
            for row in reader:
                if row["DEATHDATE"]:
                    continue
                gender = row["GENDER"]
                if gender not in ("M", "F"):
                    raise SchemaDriftError(f"{pfile.name}: column 'GENDER' has value {gender!r}")
                raw.append((row["Id"], row["BIRTHDATE"], gender, row["COUNTY"]))
        efile = csv_dir / "encounters.csv"
        with efile.open(encoding="utf-8", newline="") as fh:
            reader = csv.DictReader(fh)
            _require(reader.fieldnames, SYNTHEA_ENCOUNTER_COLUMNS, efile)
            for row in reader:
                enc[row["PATIENT"]] += 1
    counties = sorted({r[3] for r in raw})
    region_of = {c: f"R{i + 1:02d}" for i, c in enumerate(counties)}
    people = []
    for pid, bdate, sex, county in raw:
        try:
            bd = date.fromisoformat(bdate)
        except ValueError as exc:
            raise SchemaDriftError(f"patients.csv: column 'BIRTHDATE' has value {bdate!r}") from exc
        people.append(PopulationPerson(pid, bd, sex, region_of[county], enc[pid]))
    people.sort(key=lambda p: p.person_id)
    return people


def write_sample(people: list[PopulationPerson], path: Path = SAMPLE_PATH) -> None:
    buf = io.StringIO(newline="")
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(SAMPLE_COLUMNS)
    for p in people:
        w.writerow([p.person_id, p.birth_date.isoformat(), p.sex, p.region, p.encounters])
    path.parent.mkdir(parents=True, exist_ok=True)
    # mtime=0 keeps the gzip bytes identical between runs
    path.write_bytes(gzip.compress(buf.getvalue().encode("utf-8"), mtime=0))


def read_sample(path: Path = SAMPLE_PATH) -> list[PopulationPerson]:
    with gzip.open(path, "rt", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        _require(reader.fieldnames, SAMPLE_COLUMNS, path)
        out = []
        for row in reader:
            out.append(
                PopulationPerson(
                    row["person_id"],
                    date.fromisoformat(row["birth_date"]),
                    row["sex"],
                    row["region"],
                    int(row["encounters"]),
                )
            )
    return out


# ----------------------------------------------------------------------------- native


# ASSUMPTION: an age pyramid chosen by the author, not drawn from any real population.
NATIVE_AGE_BANDS = [(0, 5, 0.07), (5, 18, 0.15), (18, 30, 0.22), (30, 45, 0.27),
                    (45, 60, 0.18), (60, 80, 0.09), (80, 95, 0.02)]  # fmt: skip


def native_population(n: int, seed: int) -> list[PopulationPerson]:
    """Native generator fallback with the same schema as the Synthea adapter."""
    g = rng(seed, "native_population")
    bands = np.array([b[2] for b in NATIVE_AGE_BANDS])
    band_idx = g.choice(len(NATIVE_AGE_BANDS), size=n, p=bands / bands.sum())
    people = []
    for i in range(n):
        lo, hi, _ = NATIVE_AGE_BANDS[int(band_idx[i])]
        age_days = int(g.integers(lo * 365, hi * 365))
        bd = REFERENCE_DATE - timedelta(days=age_days)
        sex = "M" if g.random() < 0.5 else "F"
        region = f"R{int(g.integers(1, 15)):02d}"
        people.append(PopulationPerson(f"N{i:06d}", bd, sex, region, int(g.poisson(8))))
    return people


def reweight(people: list[PopulationPerson], n: int, seed: int,
             male_share: float = 0.6) -> list[PopulationPerson]:
    """Optional re weighting (ASSUMPTION): resample with a chosen male share.

    Offered for experiments only. The default build does not re weight, and no claim is
    made that any target matches a real population.
    """
    g = rng(seed, "reweight")
    males = [p for p in people if p.sex == "M"]
    females = [p for p in people if p.sex == "F"]
    n_m = round(n * male_share)
    pick_m = g.choice(len(males), size=min(n_m, len(males)), replace=False)
    pick_f = g.choice(len(females), size=min(n - len(pick_m), len(females)), replace=False)
    out = [males[int(i)] for i in pick_m] + [females[int(i)] for i in pick_f]
    return sorted(out, key=lambda p: p.person_id)
