"""Portable typed location selection, lookup and authoritative major resolution."""

import json
from functools import lru_cache
from importlib.resources import files
from typing import Literal

import cheapwings_core as _core
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
    return _core.fold(value)


class LocationCatalog:
    def __init__(self, data):
        self.data = data
        self.version = data["version"]
        self.entities = {e["id"]: e for e in data["entities"]}
        self._core = _core.LocationCatalog(json.dumps(data, ensure_ascii=False))
        self.airports = {e["code"]: e for e in data["entities"] if e["type"] == "airport"}
        self.metro_only_codes = {
            e["id"].rsplit(":", 1)[-1]
            for e in self.entities.values()
            if e["id"].startswith("metro:")
        } - self.airports.keys()

    def search(self, text: str, location_id: str | None = None):
        """Full deterministic matches; return the existing complete catalog records."""
        return [self.entities[id] for id in self._core.search(text, location_id)]

    def get_airports(self, location_id):
        return [self.entities[id] for id in self._core.airports_of(location_id)]

    def resolve(self, selection: MajorSelection) -> MajorResolution:
        codes, rationale, definition = self._core.resolve(
            selection.type, selection.location_id, selection.catalog_version
        )
        return MajorResolution(
            selection=selection, codes=codes, rationale=rationale, definition=definition
        )


@lru_cache(maxsize=1)
def catalog() -> LocationCatalog:
    return LocationCatalog(json.loads(files(__package__).joinpath("catalog.json").read_text()))
