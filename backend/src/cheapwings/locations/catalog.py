"""Portable typed location selection, lookup and authoritative major resolution."""

import json
import unicodedata
from functools import lru_cache
from importlib.resources import files
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class MajorSelection(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["city", "country"]
    location_id: str = Field(min_length=1, max_length=512)
    coverage_mode: Literal["major"] = "major"
    catalog_version: str = Field(min_length=1, max_length=64)


class MajorResolution(BaseModel):
    selection: MajorSelection
    codes: list[str]
    rationale: str
    definition: str


def fold(value: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFKD", value).casefold() if not unicodedata.combining(c)
    )


class LocationCatalog:
    def __init__(self, data):
        self.data = data
        self.version = data["version"]
        self.entities = {e["id"]: e for e in data["entities"]}
        if len(self.entities) != len(data["entities"]):
            raise ValueError("Duplicate location ID")
        self.airports = {e["code"]: e for e in data["entities"] if e["type"] == "airport"}
        if len(self.airports) != sum(e["type"] == "airport" for e in data["entities"]):
            raise ValueError("Duplicate airport code")
        self.metro_only_codes = {
            e["id"].rsplit(":", 1)[-1]
            for e in self.entities.values()
            if e["id"].startswith("metro:")
        } - self.airports.keys()
        for e in self.entities.values():
            if (
                len(e["codes"]) != len(set(e["codes"]))
                or not set(e["codes"]) <= self.airports.keys()
            ):
                raise ValueError("Invalid airport association")
        for id, mapping in data["major"].items():
            if id not in self.entities or self.entities[id]["type"] == "airport":
                raise ValueError("Invalid mapping ID")
            if (
                not mapping["codes"]
                or len(mapping["codes"]) != len(set(mapping["codes"]))
                or not set(mapping["codes"]) <= set(self.entities[id]["codes"])
            ):
                raise ValueError("Invalid major mapping")
        self.index = [
            (
                e,
                fold(
                    " ".join(
                        [
                            e["name"],
                            e.get("code", ""),
                            e.get("city", ""),
                            e["country_name"],
                            *e["aliases"],
                        ]
                    )
                ),
            )
            for e in self.entities.values()
        ]

    def search(self, text: str, location_id: str | None = None):
        """Full deterministic matches. Presentation may paginate; selection never truncates."""
        if len(text) > 100:
            raise ValueError("Search text exceeds 100 characters")
        term = fold(text.strip())
        allowed = None if location_id is None else {e["id"] for e in self.get_airports(location_id)}
        matches = [
            e
            for e, key in self.index
            if (allowed is None or e["id"] in allowed)
            and (term and term in key or allowed is not None and not term)
        ]
        return sorted(
            matches,
            key=lambda e: (
                0 if term == fold(e.get("code", "")) else 1,
                0 if term == fold(e["name"]) or term in [fold(a) for a in e["aliases"]] else 1,
                e["type"],
                fold(e["name"]),
                e["id"],
            ),
        )

    def get_airports(self, location_id):
        if location_id not in self.entities:
            raise ValueError("Unknown location ID; reload the catalog")
        return [self.airports[c] for c in self.entities[location_id]["codes"]]

    def resolve(self, selection: MajorSelection) -> MajorResolution:
        if selection.catalog_version != self.version:
            raise ValueError("Stale catalog version; reload and review the included airports")
        entity = self.entities.get(selection.location_id)
        if entity is None or entity["type"] != selection.type:
            raise ValueError("Unknown location ID or mismatched location type")
        mapping = self.data["major"].get(selection.location_id)
        if mapping is None:
            raise ValueError("No curated major-airport mapping; use Specific Airports")
        return MajorResolution(
            selection=selection,
            codes=sorted(mapping["codes"]),
            rationale=mapping["rationale"],
            definition=self.data["definition"],
        )


@lru_cache(maxsize=1)
def catalog() -> LocationCatalog:
    return LocationCatalog(json.loads(files(__package__).joinpath("catalog.json").read_text()))
