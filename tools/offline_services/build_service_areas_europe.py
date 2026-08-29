#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import osmium
except ImportError as exc:
    raise SystemExit("Modulo 'osmium' non installato. Esegui: python -m pip install osmium") from exc

ACCEPTED_HIGHWAYS = {"services", "rest_area"}
KEEP_TAGS = {
    "name", "operator", "brand", "highway", "ref", "direction",
    "destination", "destination:ref", "access", "hgv", "toilets",
    "shower", "restaurant", "fast_food", "drinking_water",
    "opening_hours", "fee", "lit", "wheelchair", "internet_access",
    "fuel", "compressed_air", "charging_station", "parking"
}


def parse_bool(value):
    if value is None:
        return None
    value = str(value).strip().lower()
    if value in {"yes", "true", "1", "designated"}:
        return True
    if value in {"no", "false", "0"}:
        return False
    return None


def safe_text(tags, key, default=None):
    try:
        value = tags.get(key)
    except Exception:
        return default
    if value is None:
        return default
    value = str(value).strip()
    return value if value else default


class ServiceAreaHandler(osmium.SimpleHandler):
    def __init__(self):
        super().__init__()
        self.rows = []

    def _append(self, osm_type, osm_id, tags, lat, lon):
        highway = safe_text(tags, "highway")
        if highway not in ACCEPTED_HIGHWAYS:
            return

        name = (
            safe_text(tags, "name")
            or safe_text(tags, "operator")
            or safe_text(tags, "brand")
            or ""
        )

        item = {
            "id": f"osm:{osm_type}/{osm_id}",
            "osmType": osm_type,
            "osmId": int(osm_id),
            "name": name,
            "type": highway,
            "lat": round(float(lat), 7),
            "lon": round(float(lon), 7),
            "roadRef": safe_text(tags, "ref"),
            "directionRaw": safe_text(tags, "direction") or safe_text(tags, "destination"),
            "hgv": safe_text(tags, "hgv", "unknown"),
            "access": safe_text(tags, "access", "unknown"),
            "facilities": {
                "toilets": parse_bool(safe_text(tags, "toilets")),
                "shower": parse_bool(safe_text(tags, "shower")),
                "restaurant": parse_bool(safe_text(tags, "restaurant")),
                "drinkingWater": parse_bool(safe_text(tags, "drinking_water")),
                "fuel": parse_bool(safe_text(tags, "fuel")),
            },
            "tags": {
                key: str(tags.get(key))
                for key in KEEP_TAGS
                if tags.get(key) is not None
            },
        }
        self.rows.append(item)

    def node(self, node):
        if safe_text(node.tags, "highway") not in ACCEPTED_HIGHWAYS:
            return
        if node.location.valid():
            self._append("node", node.id, node.tags, node.location.lat, node.location.lon)

    def way(self, way):
        if safe_text(way.tags, "highway") not in ACCEPTED_HIGHWAYS:
            return

        coords = []
        for node in way.nodes:
            try:
                if node.location.valid():
                    coords.append((node.location.lat, node.location.lon))
            except Exception:
                continue

        if not coords:
            return

        lat = sum(p[0] for p in coords) / len(coords)
        lon = sum(p[1] for p in coords) / len(coords)
        self._append("way", way.id, way.tags, lat, lon)


def main():
    if len(sys.argv) != 4:
        raise SystemExit(
            "Uso: build_service_areas_europe.py COUNTRY INPUT.osm.pbf OUTPUT.json"
        )

    country = sys.argv[1].upper().strip()
    input_path = Path(sys.argv[2])
    output_path = Path(sys.argv[3])

    if len(country) != 2:
        raise SystemExit(f"Codice Paese non valido: {country}")
    if not input_path.is_file() or input_path.stat().st_size == 0:
        raise SystemExit(f"PBF mancante o vuoto: {input_path}")

    handler = ServiceAreaHandler()
    handler.apply_file(str(input_path), locations=True, idx="flex_mem")

    # Deduplica per ID OSM.
    unique = {row["id"]: row for row in handler.rows}
    rows = list(unique.values())
    rows.sort(key=lambda x: (x["type"], x["name"].lower(), x["id"]))

    if not rows:
        raise SystemExit(f"Nessuna area di servizio trovata per {country}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schemaVersion": 6,
        "country": country,
        "generatedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source": "OpenStreetMap / Geofabrik",
        "policy": {
            "acceptedHighway": sorted(ACCEPTED_HIGHWAYS),
            "genericParkingExcluded": True,
            "graphRequired": False,
        },
        "count": len(rows),
        "areas": rows,
    }

    tmp = output_path.with_suffix(output_path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, separators=(",", ":"))
        fh.write("\n")
    tmp.replace(output_path)

    print(f"{country}: {len(rows)} aree -> {output_path}")


if __name__ == "__main__":
    main()
