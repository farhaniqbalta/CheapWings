"""Offline build: pinned airportsdata + committed country labels and editorial mappings.

Run from repo root with a Python environment containing airportsdata==20261103.
No provider/network calls. Generated backend and web catalogs must be identical.
"""

import csv
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import quote

import airportsdata

ROOT = Path(__file__).resolve().parents[1]


def build():
    if airportsdata.__version__ != "20261103":
        raise ValueError("Catalog build requires airportsdata==20261103")
    source = Path(airportsdata.__file__).parent
    curation = json.loads((ROOT / "docs/catalog/curation.json").read_text())
    countries = dict(
        line.split("\t", 1)
        for line in (ROOT / "docs/catalog/countries-tzdb-2025-07-01.tab").read_text().splitlines()
        if line and not line.startswith("#")
    )
    countries["XK"] = "Kosovo"
    with (source / "airports.csv").open(encoding="utf8") as file:
        raw_codes = [row["iata"] for row in csv.DictReader(file) if row["iata"]]
    if len(raw_codes) != len(set(raw_codes)):
        raise ValueError("Duplicate IATA codes in source CSV; review before building")
    airports = airportsdata.load("IATA")
    entities = []

    def entity(id, type, name, country, codes, aliases=(), **extra):
        entities.append(
            dict(
                id=id,
                type=type,
                name=name,
                country=country,
                country_name=countries[country],
                codes=sorted(codes),
                aliases=sorted(set(aliases)),
                **extra,
            )
        )

    for code, a in sorted(airports.items()):
        if not re.fullmatch(r"[A-Z]{3}", code):
            raise ValueError(f"Invalid physical IATA {code}")
        entity(
            f"airport:{code}",
            "airport",
            a["name"],
            a["country"],
            [code],
            curation["airport_aliases"].get(code, []),
            code=code,
            city=a["city"] or "Municipality unknown",
            region=a["subd"],
            latitude=a["lat"],
            longitude=a["lon"],
            timezone=a["tz"],
            provenance="airportsdata:20261103",
            status="listed_iata",
            scheduled_service=None,
        )
    for country in sorted({a["country"] for a in airports.values()}):
        entity(
            f"country:{country}",
            "country",
            countries[country],
            country,
            [code for code, a in airports.items() if a["country"] == country],
            curation["country_aliases"].get(country, []) + [country],
        )
    associated = set()
    for code, metro in sorted(airportsdata.load_iata_macs().items()):
        entity(
            f"metro:{metro['country']}:{code}",
            "city",
            metro["name"],
            metro["country"],
            metro["airports"],
            [code],
            region="Metro area",
        )
        associated.update(metro["airports"])
    groups = {}
    for code, a in airports.items():
        if code not in associated and a["city"].strip():
            key = (a["country"], a["subd"], a["city"])
            groups.setdefault(key, []).append(code)
    for (country, region, city), codes in sorted(groups.items()):
        # Encode full labels: no slug collisions or accidental merging of same-name cities.
        id = f"city:{country}:{quote(region, safe='')}:{quote(city, safe='')}"
        entity(id, "city", city, country, codes, region=region)
    by_id = {e["id"]: e for e in entities}
    if len(by_id) != len(entities):
        raise ValueError("Duplicate catalog IDs")
    for id, mapping in curation["major"].items():
        if (
            id not in by_id
            or not mapping["codes"]
            or len(set(mapping["codes"])) != len(mapping["codes"])
            or not set(mapping["codes"]) <= set(by_id[id]["codes"])
        ):
            raise ValueError(f"Invalid major mapping {id}")
    # Include source byte hashes so provenance can be audited even after a package refresh.
    result = {
        "version": curation["version"],
        "source": "airportsdata:20261103",
        "source_hashes": {
            name: hashlib.sha256((source / name).read_bytes()).hexdigest()
            for name in ("airports.csv", "iata_macs.csv")
        },
        "definition": curation["definition"],
        "entities": entities,
        "major": curation["major"],
    }
    content = json.dumps(result, ensure_ascii=False, separators=(",", ":")) + "\n"
    for output in (
        "backend/src/cheapwings/locations/catalog.json",
        "apps/web/public/locations.json",
    ):
        (ROOT / output).write_text(content)
    license_text = (ROOT / "docs/catalog/airportsdata-LICENSE").read_text()
    for output in (
        "backend/src/cheapwings/locations/LICENSE.txt",
        "apps/web/public/locations-LICENSE.txt",
    ):
        (ROOT / output).write_text(license_text)
    print(
        f"{len(airports)} airports; {len(entities)} typed entities; {len(curation['major'])} mappings"
    )


if __name__ == "__main__":
    build()
