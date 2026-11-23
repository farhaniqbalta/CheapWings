"""Search query validation. One-way, single adult, economy only for MVP."""

from __future__ import annotations

import json
import re
from datetime import date
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field, field_validator, model_validator

from cheapwings.domain.scope import plan_scope
from cheapwings.locations.catalog import MajorSelection

_IATA_RE = re.compile(r"^[A-Z]{3}$")


class MaxStops(str, Enum):
    ANY = "any"
    NONSTOP = "0"
    ONE = "1"
    TWO = "2"


class QueryValidationError(ValueError):
    """Raised with an actionable reason; never silently drops/narrows a query."""


class SearchQuery(BaseModel):
    trip_type: str = Field(default="one_way")
    origin_selection: MajorSelection | None = None
    destination_selection: MajorSelection | None = None
    origins: list[str]
    destinations: list[str]
    departure_date_from: date
    departure_date_through: date
    adults: int = Field(default=1)
    cabin: str = Field(default="economy")
    include_basic_economy: bool = True
    max_stops: MaxStops = MaxStops.ANY
    checked_bags_required: bool = False
    display_currency: str
    point_of_sale_country: str | None = None
    include_hidden_city: bool = False

    max_combinations: int = Field(default=120, exclude=True)

    @field_validator("origins", "destinations")
    @classmethod
    def _normalize_iata_list(cls, codes: list[str]) -> list[str]:
        if not codes:
            raise QueryValidationError("At least one airport code is required")
        normalized = []
        seen = set()
        for code in codes:
            upper = code.strip().upper()
            if not _IATA_RE.match(upper):
                raise QueryValidationError(f"Invalid IATA code: {code!r}")
            if upper not in seen:
                seen.add(upper)
                normalized.append(upper)
        return normalized

    @field_validator("trip_type")
    @classmethod
    def _one_way_only(cls, value: str) -> str:
        if value != "one_way":
            raise QueryValidationError(f"Unsupported trip_type {value!r}; only one_way in MVP")
        return value

    @field_validator("adults")
    @classmethod
    def _single_adult_only(cls, value: int) -> int:
        if value != 1:
            raise QueryValidationError(f"Unsupported adults={value}; only 1 adult in MVP")
        return value

    @field_validator("cabin")
    @classmethod
    def _economy_only(cls, value: str) -> str:
        if value != "economy":
            raise QueryValidationError(f"Unsupported cabin {value!r}; only economy in MVP")
        return value

    @field_validator("display_currency")
    @classmethod
    def _currency_shape(cls, value: str) -> str:
        upper = value.strip().upper()
        if len(upper) != 3 or not upper.isalpha():
            raise QueryValidationError(f"Invalid currency code: {value!r}")
        return upper

    @model_validator(mode="after")
    def _cross_field_rules(self) -> SearchQuery:
        if self.departure_date_through < self.departure_date_from:
            raise QueryValidationError(
                "departure_date_through must not be before departure_date_from"
            )
        if len(self.origins) == len(self.destinations) == 1 and self.origins == self.destinations:
            raise QueryValidationError(
                f"origin and destination cannot both be {self.origins[0]!r}"
            )
        n = self.combination_count()
        if n > self.max_combinations:
            raise QueryValidationError(
                f"{n} origin x destination x date combinations exceeds the configured "
                f"maximum of {self.max_combinations}; narrow the airports or date range"
            )
        return self

    def combination_count(self) -> int:
        return plan_scope(self.origins, self.destinations, self.departure_date_from,
                          self.departure_date_through)["combinations"]


class DiscoverQuery(BaseModel):
    """P7.4 Discover: origins and a departure window; destinations come from a discovery source.

    Validation (codes, dates, currency, budget, the 31-call cap) is the shared Rust core's
    `discovery_calls`. The fixed Search fields are kept so detailed checks, cache keys and result
    storage read a Discover job exactly like a Search job.
    """

    origins: list[str]
    departure_date_from: date
    departure_date_through: date
    display_currency: str
    budget: Decimal | None = None
    max_stops: MaxStops = MaxStops.ANY
    include_hidden_city: bool = False
    trip_type: str = "one_way"
    adults: int = 1
    cabin: str = "economy"
    include_basic_economy: bool = True
    checked_bags_required: bool = False
    point_of_sale_country: str | None = None

    def core_query(self) -> dict:
        return {
            "origins": self.origins,
            "date_from": self.departure_date_from.isoformat(),
            "date_through": self.departure_date_through.isoformat(),
            "display_currency": self.display_currency,
            "budget": None if self.budget is None else str(self.budget),
            "include_hidden_city": self.include_hidden_city,
        }

    def calls(self) -> list[dict]:
        """`[{origin, date}]`: one discovery call per origin and day."""
        from cheapwings._core import core

        try:
            return json.loads(core.discovery_calls(json.dumps(self.core_query())))
        except ValueError as exc:
            raise QueryValidationError(str(exc)) from None

    @model_validator(mode="after")
    def _validate_in_core(self) -> DiscoverQuery:
        calls = self.calls()
        self.origins = list(dict.fromkeys(c["origin"] for c in calls))
        return self
