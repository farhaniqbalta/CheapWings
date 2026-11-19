"""Complete host-result parity against pre-cutover provider references."""

from dataclasses import asdict
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

import cheapwings_core as core
import pytest
from backend.tests.references.fli import FliProvider as ReferenceFli
from backend.tests.references.skiplagged import SkiplaggedProvider as ReferenceSkiplagged

from cheapwings.domain.evidence import ProviderFailure
from cheapwings.providers.base import SingleDateRouteQuery
from cheapwings.providers.common import json_payload
from cheapwings.providers.fli import FliProvider
from cheapwings.providers.skiplagged import SkiplaggedProvider

NOW = datetime(2026, 11, 19, tzinfo=UTC)


class Clock(datetime):
    @classmethod
    def now(cls, tz=None):
        return NOW


def fli_payload(
    amount=Decimal("1250000.123456789"),
    currency="IDR",
    origin="HND",
    destination="CGK",
    day=date(2027, 1, 2),
):
    import base64

    token = base64.urlsafe_b64encode(b"\x1a\x05\x1a\x03" + currency.encode()).decode().rstrip("=")
    leg = [None] * 23
    leg[3], leg[6], leg[8], leg[10], leg[11] = origin, destination, [9, 0], [15, 0], 360
    leg[20] = leg[21] = [day.year, day.month, day.day]
    leg[22] = ["TR", "801", "SQ"]
    detail = [None] * 10
    detail[2], detail[9] = [leg], 360
    return {
        "data": [None, None, [[[detail, [[None, amount], token]]]], None],
        "url": "https://www.google.com/travel/flights?tfs=synthetic",
    }


def test_parser_bindings_exist():
    assert hasattr(core, "fli_parse")
    assert hasattr(core, "skiplagged_parse")


def outcome(provider, payload, q):
    try:
        return asdict(provider.normalize(payload, q))
    except ProviderFailure as exc:
        return exc.code
    except (ValueError, TypeError, IndexError, KeyError, AttributeError):
        return "schema_changed"


@pytest.mark.parametrize(
    "mutation",
    [
        "normal",
        "operator",
        "precision",
        "float",
        "bool",
        "negative",
        "zero",
        "unpriced",
        "bad_currency",
        "mixed_currency",
        "currency_then_malformed",
        "row_limit",
        "bad_route",
        "bad_link",
        "no_legs",
        "unknown_carrier",
        "numeric_flight_number",
        "bad_date",
        "bad_duration",
        "bad_leg_duration",
        "empty",
        "missing_group",
    ],
)
def test_fli_complete_result_parity(mutation):
    require_fli()
    payload = fli_payload()
    row = payload["data"][2][0][0]
    leg = row[0][2][0]
    if mutation == "operator":
        leg[22][2] = "QF"
    if mutation == "precision":
        leg[8] = [9, 0, 1, 123456]
        leg[10] = [15, 0, 2, 654321]
    if mutation in ("float", "bool", "negative", "zero"):
        row[1][0][-1] = {"float": 1.2, "bool": True, "negative": Decimal(-1), "zero": 0}[mutation]
    if mutation == "unpriced":
        row[1][0] = []
    if mutation == "bad_currency":
        payload = fli_payload(currency="USD")
    if mutation == "currency_then_malformed":
        payload = fli_payload(currency="USD")
        payload["data"][2][0].append(None)
    if mutation == "mixed_currency":
        payload["data"][3] = fli_payload(currency="USD")["data"][2]
    if mutation == "row_limit":
        payload["data"][2][0] *= 501
    if mutation == "bad_route":
        leg[3] = "NRT"
    if mutation == "bad_link":
        payload["url"] = "https://evil.example/travel/flights"
    if mutation == "no_legs":
        row[0][2] = []
    if mutation == "unknown_carrier":
        leg[22][0] = "ZZZ"
    if mutation == "numeric_flight_number":
        leg[22][1] = 801
    if mutation == "bad_duration":
        row[0][9] = 0
    if mutation == "bad_leg_duration":
        leg[11] = -1
    if mutation == "bad_date":
        leg[20] = [2027, 2, 30]
    if mutation == "empty":
        payload["data"][2] = [[]]
    if mutation == "missing_group":
        payload["data"][2] = None
    q = SingleDateRouteQuery("HND", "CGK", date(2027, 1, 2), True, False, "IDR")
    providers = [FliProvider(), ReferenceFli()]
    try:
        with (
            patch("cheapwings.providers.fli.datetime", Clock),
            patch("backend.tests.references.fli.datetime", Clock),
        ):
            assert outcome(providers[0], payload, q) == outcome(providers[1], payload, q)
    finally:
        for p in providers:
            p.blocking.close()


@pytest.mark.parametrize(
    "mutation",
    [
        "normal",
        "fractional",
        "offset",
        "compact_offset",
        "offset_seconds",
        "negative",
        "string_price",
        "wrong_route",
        "bad_link",
        "no_currency",
        "missing_time",
        "naive",
        "invalid_date",
        "invalid_stops",
        "empty",
        "partial",
    ],
)
def test_skiplagged_complete_result_parity(mutation):
    source = (
        Path(__file__).resolve().parents[3]
        / "contracts/fixtures/provider/skiplagged_probe_20261109T123430Z.json"
    )
    payload = json_payload(source.read_text())["search_structured_content"]
    card = payload["flights"][0]
    if mutation == "fractional":
        card["departure"]["dateTime"] = "2026-12-16T07:00:00.999999+11:00"
        card["arrival"]["dateTime"] = "2026-12-16T12:00:00.000001+08:00"
    if mutation == "offset":
        card["departure"]["dateTime"] = "2026-12-16T07:00:00+05:45"
    if mutation == "compact_offset":
        card["departure"]["dateTime"] = "2026-12-16T07:00:00+0545"
    if mutation == "offset_seconds":
        card["departure"]["dateTime"] = "2026-12-16T07:00:00+05:45:30.25"
    if mutation == "negative":
        card["price"]["usdAmount"] = -1
    if mutation == "string_price":
        card["price"]["usdAmount"] = "271.50000000001"
    if mutation == "wrong_route":
        card["departure"]["airport"] = "SYD"
    if mutation == "bad_link":
        card["deepLink"] = "https://evil.example/"
    if mutation == "no_currency":
        payload["pricing"]["currency"] = "XYZ"
    if mutation == "missing_time":
        card["departure"].pop("dateTime")
    if mutation == "naive":
        card["departure"]["dateTime"] = "2026-12-16T07:00:00"
    if mutation == "invalid_date":
        card["departure"]["dateTime"] = "2026-02-30T07:00:00+11:00"
    if mutation == "invalid_stops":
        card["layovers"] = True
    if mutation == "empty":
        payload["flights"] = []
    if mutation == "partial":
        payload["pagination"] = {"hasMoreResults": True}
    q = SingleDateRouteQuery("MEL", "DPS", date(2026, 12, 16), True, False, "IDR")
    with (
        patch("cheapwings.providers.skiplagged.datetime", Clock),
        patch("backend.tests.references.skiplagged.datetime", Clock),
    ):
        assert outcome(SkiplaggedProvider(), payload, q) == outcome(
            ReferenceSkiplagged(), payload, q
        )


def require_fli():
    try:
        from fli.search import _decoders
    except ImportError:
        pytest.fail('Fli parity requires pip install -e "backend[live]"', pytrace=False)
    assert callable(_decoders.parse_flight_row)


def test_recorded_fli_page():
    require_fli()
    import json

    path = Path(__file__).resolve().parents[3] / "contracts/fixtures/provider/fli_recorded_ds1.json"
    fixture = json.loads(path.read_text())
    payload = {"data": json_payload(fixture["data_json"])}
    q = SingleDateRouteQuery(
        fixture["origin"],
        fixture["destination"],
        date.fromisoformat(fixture["date"]),
        True,
        False,
        fixture["currency"],
    )
    providers = [FliProvider(), ReferenceFli()]
    try:
        with (
            patch("cheapwings.providers.fli.datetime", Clock),
            patch("backend.tests.references.fli.datetime", Clock),
        ):
            for provider in providers:
                normalized = json.loads(
                    json.dumps(asdict(provider.normalize(payload, q)), default=str)
                )
                assert normalized == fixture["web"]
    finally:
        for provider in providers:
            provider.blocking.close()
