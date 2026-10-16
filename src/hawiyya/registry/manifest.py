"""Data manifest: source, versions, commands and hashes of every committed data file."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from hawiyya.core.determinism import sha256_file
from hawiyya.core.paths import DATA, PRIVATE, ROOT
from hawiyya.registry import source
from hawiyya.registry.synthea import JAR_NAME, synthea_command

MANIFEST = DATA / "MANIFEST.json"
HASHED_FILES = (
    "data/samples/population.csv.gz",
    "data/lexicon/names.json",
    "data/lexicon/denylist.json",
)


def _relative_command(seed: int, population: int, chunk: int) -> list[str]:
    jar = Path(".sikka/tools") / JAR_NAME
    out = Path(".sikka/synthea") / f"chunk{chunk:02d}"
    return [c.replace("\\", "/") for c in synthea_command(jar, out, seed, population)]


def derive_synthea_sample(base: Path | None = None) -> dict[str, Any]:
    """Read the Synthea chunks, write the committed derived sample, return provenance."""
    base = base or PRIVATE / "synthea"
    people = source.read_synthea_chunks(base)
    source.write_sample(people)
    chunks = []
    for done in sorted(base.glob("chunk*/DONE.json")):
        meta = json.loads(done.read_text(encoding="utf-8"))
        chunks.append({
            "chunk": meta["chunk"], "seed": meta["seed"], "population": meta["population"],
            "command": _relative_command(meta["seed"], meta["population"], meta["chunk"]),
            "patients_csv_sha256": meta["patients_sha256"],
        })  # fmt: skip
    release_file = PRIVATE / "tools" / "synthea_release.json"
    release = json.loads(release_file.read_text(encoding="utf-8")) if release_file.exists() else {}
    return {
        "release_tag": release.get("tag"),
        "release_url": release.get("url"),
        "jar_sha256": release.get("sha256"),
        "reference_date": source.REFERENCE_DATE.isoformat(),
        "chunks": chunks,
        "alive_patients_kept": len(people),
        "columns_kept": list(source.SAMPLE_COLUMNS),
    }


def write_manifest(data_source: str, provenance: dict[str, Any], lexicon_author: str,
                   cowork: dict[str, Any]) -> dict[str, Any]:
    files = {f: sha256_file(str(ROOT / f)) for f in HASHED_FILES if (ROOT / f).exists()}
    manifest = {
        "data_source": data_source,
        "data_source_label": "Synthea" if data_source == "synthea" else "native generator",
        "note": "All patients and identifiers are synthetic. Synthea supplies only birth date, "
        "sex, a coarse region and an encounter count; names and identifiers come from the "
        "identity layer in this repository.",
        "provenance": provenance,
        "lexicon_author": lexicon_author,
        "cowork_inputs": cowork,
        "files_sha256": files,
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8", newline="\n")
    return manifest


def load_manifest() -> dict[str, Any]:
    data: dict[str, Any] = json.loads(MANIFEST.read_text(encoding="utf-8"))
    return data


def verify_manifest() -> list[str]:
    """Return the files whose hash does not match the manifest."""
    m = load_manifest()
    return [f for f, h in m["files_sha256"].items() if sha256_file(str(ROOT / f)) != h]
