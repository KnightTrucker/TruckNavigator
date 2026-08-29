#!/usr/bin/env python3
import datetime
import glob
import hashlib
import json
import os

EXPECTED = {"IT", "FR", "DE", "CH", "AT", "BE", "LU", "NL", "ES"}

out = {
    "schemaVersion": 2,
    "generatedAt": datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z"),
    "mode": "route-proximity",
    "countries": {}
}

for p in sorted(glob.glob("offline/service_areas/*.json")):
    name = os.path.basename(p)
    if name.endswith(".graph.json"):
        continue
    cc = os.path.splitext(name)[0]
    if cc not in EXPECTED:
        continue

    with open(p, "rb") as f:
        raw = f.read()

    data = json.loads(raw)
    areas = data.get("areas")
    if not isinstance(areas, list):
        raise SystemExit(f"{p}: campo areas non valido")
    if data.get("count") != len(areas):
        raise SystemExit(f"{p}: count non coerente")

    out["countries"][cc] = {
        "count": len(areas),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "file": f"{cc}.json"
    }

os.makedirs("offline/service_areas", exist_ok=True)
with open("offline/service_areas/manifest_europe.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)

print(json.dumps(out, ensure_ascii=False, indent=2))
