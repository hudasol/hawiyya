"""Synthea build time tooling: fetch the release jar and run it with a fixed seed.

Synthea (https://github.com/synthetichealth/synthea, Apache License 2.0) is used only at
build time to produce a synthetic population. The jar lives in ``.sikka/tools/`` and is
never committed. Only standard library modules are used so this file can run before the
project dependencies are installed.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import time
import urllib.request
from pathlib import Path

API_LATEST = "https://api.github.com/repos/synthetichealth/synthea/releases/latest"
JAR_NAME = "synthea-with-dependencies.jar"
USER_AGENT = "hawiyya-build (synthetic data generator)"


def _get(url: str, timeout: int) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data: bytes = resp.read()
        return data


def latest_release(timeout: int = 60) -> dict[str, str]:
    """Return the tag and jar download url of the latest Synthea release."""
    info = json.loads(_get(API_LATEST, timeout))
    for asset in info.get("assets", []):
        if asset.get("name") == JAR_NAME:
            return {"tag": str(info["tag_name"]), "url": str(asset["browser_download_url"])}
    raise RuntimeError("the latest Synthea release has no " + JAR_NAME)


def fetch_jar(tools_dir: Path, attempts: int = 3, timeout: int = 600) -> dict[str, str]:
    """Download the jar (retrying twice) and return tag, url, path and SHA 256."""
    tools_dir.mkdir(parents=True, exist_ok=True)
    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            rel = latest_release()
            target = tools_dir / JAR_NAME
            if not target.exists():
                tmp = target.with_suffix(".part")
                tmp.write_bytes(_get(rel["url"], timeout))
                tmp.replace(target)
            digest = hashlib.sha256(target.read_bytes()).hexdigest()
            meta = {**rel, "path": target.as_posix(), "sha256": digest}
            (tools_dir / "synthea_release.json").write_text(json.dumps(meta, indent=2))
            return meta
        except Exception as exc:  # network failures are retried, then reported
            last_error = exc
            time.sleep(5 * (attempt + 1))
    raise RuntimeError(f"Synthea download failed after {attempts} attempts: {last_error}")


REFERENCE_DATE = "20260101"


def synthea_command(jar: Path, out_dir: Path, seed: int, population: int) -> list[str]:
    """The exact Synthea command used, recorded in the manifest.

    A fixed reference date keeps birth dates identical whatever day the build runs.
    """
    return [
        "java", "-jar", str(jar),
        "-s", str(seed),
        "-cs", str(seed),
        "-r", REFERENCE_DATE,
        "-p", str(population),
        "--exporter.baseDirectory", str(out_dir),
        "--exporter.csv.export", "true",
        "--exporter.csv.included_files", "patients.csv,encounters.csv",
        "--exporter.fhir.export", "false",
        "--exporter.hospital.fhir.export", "false",
        "--exporter.practitioner.fhir.export", "false",
        "--exporter.years_of_history", "1",
        "--generate.only_alive_patients", "true",
    ]


def run_chunks(jar: Path, base: Path, seed: int, total: int, chunk: int, timeout: int) -> None:
    """Run Synthea in deterministic chunks (seed + k), skipping chunks already finished.

    Each chunk is an independent deterministic run, so a stopped build resumes without
    changing the result.
    """
    jar, base = jar.resolve(), base.resolve()
    n_chunks = (total + chunk - 1) // chunk
    for k in range(n_chunks):
        out = base / f"chunk{k:02d}"
        done = out / "DONE.json"
        if done.exists():
            continue
        size = min(chunk, total - k * chunk)
        cmd = synthea_command(jar, out, seed + k, size)
        out.mkdir(parents=True, exist_ok=True)
        with (out / "synthea_run.log").open("w", encoding="utf-8") as fh:
            subprocess.run(cmd, cwd=base, stdout=fh, stderr=subprocess.STDOUT, timeout=timeout,
                           check=True)
        csv = out / "csv" / "patients.csv"
        meta = {"chunk": k, "seed": seed + k, "population": size, "command": cmd,
                "patients_sha256": hashlib.sha256(csv.read_bytes()).hexdigest()}
        done.write_text(json.dumps(meta, indent=2), encoding="utf-8")
        print(f"chunk {k} done", flush=True)


if __name__ == "__main__":
    import sys

    if sys.argv[1] == "fetch":
        print(json.dumps(fetch_jar(Path(sys.argv[2])), indent=2))
    elif sys.argv[1] == "run":
        jar_path, base_dir = Path(sys.argv[2]), Path(sys.argv[3])
        run_chunks(jar_path, base_dir, seed=int(sys.argv[4]), total=int(sys.argv[5]),
                   chunk=int(sys.argv[6]), timeout=3600)
