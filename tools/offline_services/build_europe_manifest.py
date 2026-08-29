#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

EXPECTED = ["IT", "FR", "DE", "CH", "AT", "BE", "LU", "NL", "ES"]
BASE = Path("offline/service_areas")
OUT = BASE / "manifest_europe.json"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    countries = {}

    for cc in EXPECTED:
        path = BASE / f"{cc}.json"
        if not path.is_file() or path.stat().st_size == 0:
            raise SystemExit(f"Database mancante o vuoto: {path}")

        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)

        if data.get("country") != cc:
            raise SystemExit(f"country errato in {path}: {data.get('country')!r}")
        areas = data.get("areas")
        if not isinstance(areas, list) or not areas:
            raise SystemExit(f"areas non valido/vuoto in {path}")
        if data.get("count") != len(areas):
            raise SystemExit(f"count incoerente in {path}")

        countries[cc] = {
            "file": f"{cc}.json",
            "count": len(areas),
            "sha256": sha256(path),
            "schemaVersion": data.get("schemaVersion"),
            "generatedAt": data.get("generatedAt"),
        }

    manifest = {
        "schemaVersion": 2,
        "generatedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "graphRequired": False,
        "countries": countries,
        "totalAreas": sum(v["count"] for v in countries.values()),
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUT.with_suffix(".json.tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    tmp.replace(OUT)

    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
