"""Generate the shared Rust-core fixtures from the Python reference engine (no network).

Run from repo root: PYTHONPATH=backend/src .venv/bin/python scripts/gen_core_fixtures.py
Writes contracts/fixtures/core/core_fixtures.json with the answers the Python reference
produces. The Rust core, its PyO3 module and its Swift package must all match them exactly.

Money answers come from the pure-Decimal reference below, NOT from cheapwings.domain.money:
since P5.1 that module delegates to the Rust core, so using it would gate Rust against itself.
"""

import json
import random
import subprocess
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

rng = random.Random(20261113)

# ---------- pure-Python money reference (money.py arithmetic as of 984cfd2, before Rust) ----------

_REFERENCE_EXPONENTS = {
    "IDR": 0, "JPY": 0, "KRW": 0, "VND": 0,
    "USD": 2, "AUD": 2, "EUR": 2, "GBP": 2, "CAD": 2, "SGD": 2, "MYR": 2, "INR": 2, "CNY": 2,
    "HKD": 2, "NZD": 2, "CHF": 2, "THB": 2, "PHP": 2, "BRL": 2, "MXN": 2, "CZK": 2, "DKK": 2,
    "SEK": 2, "PLN": 2, "RON": 2, "TRY": 2, "TWD": 2, "UAH": 2,
}


def _reference_exponent(currency):
    try:
        return _REFERENCE_EXPONENTS[currency.upper()]
    except KeyError:
        raise ValueError(f"unknown currency {currency!r}") from None


def reference_fx_convert(amount, rate, quote_currency):
    quantum = Decimal(1).scaleb(-_reference_exponent(quote_currency))
    return str((Decimal(amount) * Decimal(rate)).quantize(quantum))


def reference_from_minor_units(minor, currency):
    return str(Decimal(minor).scaleb(-_reference_exponent(currency)))


def reference_as_minor_units(amount, currency):
    scaled = Decimal(amount).scaleb(_reference_exponent(currency))
    if scaled != scaled.to_integral_value():
        raise ValueError(f"{amount} does not scale cleanly")
    return int(scaled)
CURRENCIES = ["IDR", "JPY", "USD", "AUD", "EUR", "SGD", "XYZ"]
AIRPORTS = ["CGK", "DPS", "SUB", "SIN", "KUL", "NRT", "HND", "SYD", "LHR", "JFK", "KTM", "DEL"]
CARRIERS = ["GA", "QZ", "SQ", "MH", "JL", "QF", "BA", "AA", "3K", "5J"]
# Real-world offsets incl. half/quarter hours and negatives (Nepal +05:45, Newfoundland -03:30).
OFFSETS = [25200, 28800, 32400, 0, 19800, 20700, -12600, -18000, -36000, 39600]


def outcome(fn):
    try:
        return str(fn())
    except (ValueError, ArithmeticError):
        return None  # both cores must fail on this input


def money_cases(n):
    cases = []
    for _ in range(n):
        places = rng.randint(0, 6)
        amount = str(Decimal(rng.randint(-10**10, 10**10)).scaleb(-places))
        rate = str(Decimal(rng.randint(1, 10**9)).scaleb(-rng.randint(0, 10)))
        currency = rng.choice(CURRENCIES)
        minor = rng.randint(-10**12, 10**12)
        cases.append({"op": "fx", "amount": amount, "rate": rate, "currency": currency,
                      "expect": outcome(lambda: reference_fx_convert(amount, rate, currency))})
        cases.append({"op": "from_minor", "minor": str(minor), "currency": currency,
                      "expect": outcome(lambda: reference_from_minor_units(minor, currency))})
        cases.append({"op": "as_minor", "amount": amount, "currency": currency,
                      "expect": outcome(lambda: reference_as_minor_units(amount, currency))})
    for amount, rate, currency in [("0.125", "1", "USD"), ("0.135", "1", "USD"), ("2.5", "1", "IDR"),
                                   ("3.5", "1", "IDR"), ("-0.004", "1", "USD"), ("1250000", "0.0000613", "USD")]:
        cases.append({"op": "fx", "amount": amount, "rate": rate, "currency": currency,
                      "expect": outcome(lambda: reference_fx_convert(amount, rate, currency))})
    return cases


def instant():
    offset = rng.choice(OFFSETS)
    micro = rng.choice([0, 0, 0, 123000, 500, 999999])
    base = datetime(2026, rng.randint(1, 12), rng.randint(1, 28), rng.randint(0, 23), rng.randint(0, 59),
                    rng.choice([0, 0, 30, 59]), micro, tzinfo=timezone(timedelta(seconds=offset)))
    parts = {"y": base.year, "mo": base.month, "d": base.day, "h": base.hour, "mi": base.minute,
             "s": base.second, "us": base.microsecond, "offset": offset}
    return base, parts


def fingerprint_cases(n):
    from cheapwings.domain.itinerary import compute_fingerprint
    from cheapwings.domain.segments import FlightSegment

    cases = []
    for _ in range(n):
        segments, raw = [], []
        for ordinal in range(rng.randint(1, 3)):
            origin, destination = rng.sample(AIRPORTS, 2)
            depart, depart_parts = instant()
            arrive, arrive_parts = instant()
            marketing = rng.choice(CARRIERS)
            operating = rng.choice([marketing, rng.choice(CARRIERS)])
            flight = str(rng.randint(1, 9999))
            segments.append(FlightSegment(marketing, operating, flight, origin, destination, depart, arrive, ordinal))
            raw.append({"ordinal": ordinal, "marketing": marketing, "operating": operating, "flight": flight,
                        "origin": origin, "destination": destination, "depart": depart_parts, "arrive": arrive_parts})
        cases.append({"segments": raw, "expect": compute_fingerprint(tuple(segments))})
    return cases


def offer(quote_id):
    # Money here only carries amounts into Offer; ranking compares them, no money arithmetic.
    from cheapwings.domain.money import Money
    from cheapwings.domain.offer import ComparisonStatus, LinkScope, Offer, PriceStatus, ThreeValued

    status = rng.choice(list(PriceStatus))
    hidden = ThreeValued.NO if status == PriceStatus.REPRICED_EXACT else rng.choice(list(ThreeValued))
    amount = rng.choice(["99.00", "100.00", "100.00", "120.50", "120.5", "75.25", None])  # ties on purpose
    comparable = Money(Decimal(amount), "USD") if amount else None
    o = Offer(quote_id, "it", "p", None, None, "economy", None, Money(Decimal("1"), "USD"), comparable,
              rng.choice(list(ComparisonStatus)), ThreeValued.UNKNOWN, hidden, ThreeValued.UNKNOWN,
              status, False, datetime(2026, 1, 1, tzinfo=timezone.utc), None, None, LinkScope.UNAVAILABLE, None)
    return o, {"id": quote_id, "price_status": status.value, "hidden_city": hidden.value,
               "comparison_status": o.comparison_status.value, "amount": amount}


def ranking_cases(n):
    from cheapwings.engine.ranking import best_checked_deal, lowest_advertised

    cases = []
    for c in range(n):
        groups, raw = [], []
        for g in range(rng.randint(1, 5)):
            offers = [offer(f"c{c}g{g}o{i}") for i in range(rng.randint(0, 4))]
            groups.append(SimpleNamespace(offers=[o for o, _ in offers]))
            raw.append([r for _, r in offers])
        cases.append({"groups": raw,
                      "best": [r.offer.quote_id for r in best_checked_deal(groups)],
                      "lowest": [r.offer.quote_id for r in lowest_advertised(groups)]})
    return cases


def fli_tfs_cases(n):
    from fli.search._proto import encode_tfs_payload, encode_tfs_segment

    cases = []
    for _ in range(n):
        origin, destination = rng.sample(AIRPORTS, 2)
        date = f"2026-{rng.randint(1, 12):02d}-{rng.randint(1, 28):02d}"
        tfs = encode_tfs_payload(encode_tfs_segment(origin, destination, date), is_one_way=True,
                                 passengers=[1], seat=1)
        cases.append({"origin": origin, "destination": destination, "date": date, "expect": tfs})
    return cases


# Synthetic Google Flights pages in the ds:1 layout fli 881aee5 decodes (no provider payloads).
FLI_AIRPORTS = ["CGK", "DPS", "SUB", "SIN", "KUL", "NRT"]
FLI_AIRLINES = ["GA", "QZ", "SQ", "MH", "JL", "3K"]
FLI_PRICES = ["1250000", "1234.50", "980.5", "75"]


def currency_token(code):
    import base64

    inner = b"\x1a" + bytes([len(code)]) + code.encode()
    return base64.urlsafe_b64encode(b"\x1a" + bytes([len(inner)]) + inner).decode().rstrip("=")


def fli_leg(origin, destination):
    leg = [None] * 23
    leg[3], leg[6] = origin, destination
    leg[8] = [rng.randint(0, 23), rng.choice([0, 5, 30, None])]
    leg[10] = [rng.randint(0, 23), rng.choice([0, 45, None])]
    leg[11] = rng.randint(40, 600)
    leg[20] = [2026, 12, rng.randint(1, 28)]
    leg[21] = [2026, 12, rng.randint(1, 28)]
    leg[22] = [rng.choice(FLI_AIRLINES), str(rng.randint(1, 9999)), None]
    return leg


def fli_row(token):
    """Returns (row, price lexeme or None). The price is a placeholder string until rendering."""
    stops = rng.sample(FLI_AIRPORTS, rng.randint(2, 4))
    detail = [None] * 10
    detail[2] = [fli_leg(a, b) for a, b in zip(stops, stops[1:])]
    detail[9] = 120
    if rng.random() < 0.3:
        return [detail, [[], token]], None
    price = rng.choice(FLI_PRICES)
    return [detail, [[None, f"__PRICE_{price}__"], token]], price


def render_page(data_json):
    return ("<html><script>AF_initDataCallback({key: 'ds:0', hash: '1', data:[1], sideChannel: {}});</script>"
            f"<script>AF_initDataCallback({{key: 'ds:1', hash: '2', data:{data_json}, sideChannel: {{}}}});</script></html>")


def expected_offer(row, price):
    import copy

    from fli.search._decoders import parse_flight_row

    probe = copy.deepcopy(row)
    probe[1][0][-1] = 0  # same placeholder trick as providers/fli.py
    flight = parse_flight_row(probe)
    return {"price": price, "currency": flight.currency, "legs": [
        {"origin": leg.departure_airport.name.removeprefix("_"),
         "destination": leg.arrival_airport.name.removeprefix("_"),
         "airline": leg.airline.name.removeprefix("_"), "flight_number": leg.flight_number,
         "depart_local": leg.departure_datetime.strftime("%Y-%m-%dT%H:%M"),
         "arrive_local": leg.arrival_datetime.strftime("%Y-%m-%dT%H:%M")} for leg in flight.legs]}


def fli_page_cases(n):
    cases = []
    for _ in range(n):
        token = currency_token(rng.choice(["IDR", "USD"]))
        rows = [fli_row(token) for _ in range(rng.randint(1, 30))]
        split = rng.randint(0, len(rows))
        groups = [[[r for r, _ in rows[:split]]] if split else None, [[r for r, _ in rows[split:]]] if split < len(rows) else None]
        data = json.dumps([None, None, *groups])
        for _, price in rows:
            if price is not None:
                data = data.replace(f'"__PRICE_{price}__"', price, 1)
        offers = [expected_offer(r, p) for r, p in rows if p is not None]
        cases.append({"html": render_page(data),
                      "expect": {"offers": offers, "unpriced": sum(p is None for _, p in rows)}})
    many = json.dumps([None, None, [[fli_row(currency_token("IDR"))[0] for _ in range(501)]], None])
    cases += [
        {"html": "<html><script>AF_initDataCallback({key: 'ds:0', data:[1], sideChannel: {}});</script></html>",
         "expect": {"error": "schema_changed"}},
        {"html": "<html><body>Our systems have detected unusual traffic from your computer</body></html>",
         "expect": {"error": "auth_denied"}},
        {"html": render_page(many.replace('"__PRICE_', '"x').replace('__"', '"')), "expect": {"error": "partial_payload"}},
        {"html": render_page("[null, null, null, null]"), "expect": {"error": "schema_changed"}},
        {"html": render_page('[null, null, "rows", null]'), "expect": {"error": "schema_changed"}},
    ]
    return cases


PLAN_ERRORS = {  # QueryValidationError message fragment -> core PlanError code
    "At least one airport code": "no_airports",
    "Invalid IATA code": "invalid_airport",
    "must not be before": "dates_reversed",
    "cannot both be": "same_airport",
    "exceeds the configured": "too_many",
}


def planning_case(origins, destinations, start, end, max_combinations=120):
    from datetime import date

    from cheapwings.domain.query import SearchQuery
    from cheapwings.engine.expansion import expand_routes_and_dates

    case = {"origins": origins, "destinations": destinations, "from": start, "through": end,
            "max": max_combinations}
    try:
        query = SearchQuery(origins=origins, destinations=destinations,
                            departure_date_from=date.fromisoformat(start),
                            departure_date_through=date.fromisoformat(end),
                            display_currency="IDR", max_combinations=max_combinations)
    except Exception as exc:  # pydantic wraps QueryValidationError
        code = next((c for fragment, c in PLAN_ERRORS.items() if fragment in str(exc)), None)
        if code is None:
            raise
        return {**case, "expect": {"error": code}}
    combos = [{"origin": c.origin, "destination": c.destination, "date": c.departure_date.isoformat()}
              for c in expand_routes_and_dates(query)]
    return {**case, "expect": combos}


def planning_cases(n):
    from datetime import date, timedelta

    def messy(code):
        return rng.choice([code, code.lower(), f" {code} ", code.title()])

    cases = []
    starts = ["2026-12-30", "2028-02-27", "2026-06-15", "2027-01-31"]
    for _ in range(n):
        origins = [messy(c) for c in rng.sample(AIRPORTS, rng.randint(1, 3))]
        destinations = [messy(c) for c in rng.sample(AIRPORTS, rng.randint(1, 3))]
        if rng.random() < 0.2:
            origins.append(origins[0])  # duplicate after normalization
        start = date.fromisoformat(rng.choice(starts))
        end = start + timedelta(days=rng.randint(0, 14))
        cases.append(planning_case(origins, destinations, start.isoformat(), end.isoformat()))
    eleven = AIRPORTS[:11]
    cases += [
        planning_case(["CG1"], ["DPS"], "2026-12-01", "2026-12-01"),
        planning_case(["CGK"], ["DPS"], "2026-12-05", "2026-12-01"),
        planning_case(["CGK"], ["cgk"], "2026-12-01", "2026-12-01"),
        planning_case(eleven, [c for c in AIRPORTS if c not in eleven] + ["XXA", "XXB", "XXC", "XXD",
                                                                           "XXE", "XXF", "XXG", "XXH",
                                                                           "XXI", "XXJ"],
                      "2026-12-01", "2026-12-01"),
        planning_case([], ["DPS"], "2026-12-01", "2026-12-01"),
        planning_case(["CGK"], ["DPS"], "2028-02-28", "2028-03-01"),
    ]
    return cases


LOCATION_QUERIES = ["CGK", "cgk", "tokyo", "Tokyo", "jakarta", "sao paulo", "São Paulo", "zurich", "Zürich",
                    "NRT", "japan", "Indonesia", "london", "new york", "bali", "  dps  ", "xyzxyz", "ber", "a",
                    "Haneda", "osaka", "singapore", "united", "san", "los angeles", "ä", "mumbai", "Bombay"]


def location_search_cases():
    from cheapwings.locations.catalog import catalog

    cat = catalog()
    cases = []

    def case(text, within=None):
        try:
            found = cat.search(text, within)
            # P5.6: total = full match count (the picker shows "N more").
            return {"text": text, "within": within, "expect": [e["id"] for e in found][:15], "total": len(found)}
        except ValueError as exc:
            code = "too_long" if "exceeds 100" in str(exc) else "unknown_location"
            return {"text": text, "within": within, "expect": {"error": code}}

    cases += [case(q) for q in LOCATION_QUERIES]
    cases += [case("", "country:JP"), case("", "metro:JP:TYO"), case("hnd", "metro:JP:TYO"),
              case("", "airport:CGK"), case("x" * 101), case("tokyo", "nowhere:XX")]
    names = [e["name"] for e in cat.entities.values() if e["type"] != "country"]
    cases += [case(rng.choice(names)) for _ in range(20)]
    # P5.6: typed combining marks. Python drops only combining class != 0 (Mn), keeps spacing
    # marks (Mc, e.g. Devanagari "ा"), so "Tokyoा" matches nothing.
    cases += [case(q) for q in ("Tokyoा", "दिल्ली", "jakartaँ")]
    return cases


def location_major_cases():
    from cheapwings.locations.catalog import MajorSelection, catalog

    cat = catalog()

    def case(kind, location_id, version=None):
        version = version or cat.version
        entry = {"kind": kind, "id": location_id, "version": version}
        try:
            r = cat.resolve(MajorSelection(type=kind, location_id=location_id, catalog_version=version))
            return {**entry, "expect": {"codes": r.codes, "rationale": r.rationale, "definition": r.definition}}
        except ValueError as exc:
            msg = str(exc)
            if "Stale catalog" in msg:
                code = "stale_version"
            elif "No curated" in msg:
                code = "no_major_mapping"
            else:
                code = "unknown_location" if location_id not in cat.entities else "type_mismatch"
            return {**entry, "expect": {"error": code}}

    cases = [case(cat.entities[i]["type"], i) for i in sorted(cat.data["major"])]
    no_mapping = next(i for i, e in sorted(cat.entities.items()) if e["type"] == "city" and i not in cat.data["major"])
    first = sorted(cat.data["major"])[0]
    other = "city" if cat.entities[first]["type"] == "country" else "country"
    cases += [case("city", no_mapping), case(cat.entities[first]["type"], first, "old-version"),
              case(other, first), case("city", "metro:XX:NOPE")]
    return cases


def main():
    root = Path(__file__).resolve().parents[1]
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True,
                            cwd=root).stdout.strip() or "unknown"
    fixtures = {"source": f"money: pure-Decimal reference in this script; fingerprint/ranking: "
                          f"backend/src/cheapwings @ {commit}; fli 881aee5",
                "money": money_cases(1000), "fingerprint": fingerprint_cases(500),
                "ranking": ranking_cases(300), "fli_tfs": fli_tfs_cases(50), "fli_pages": fli_page_cases(40),
                "planning": planning_cases(60), "location_search": location_search_cases(),
                "location_major": location_major_cases()}
    out = root / "contracts" / "fixtures" / "core" / "core_fixtures.json"
    out.write_text(json.dumps(fixtures, separators=(",", ":")))
    print(f"wrote {out.name}: {len(fixtures['money'])} money, {len(fixtures['fingerprint'])} fingerprint, "
          f"{len(fixtures['ranking'])} ranking, {len(fixtures['fli_tfs'])} fli_tfs, "
          f"{len(fixtures['fli_pages'])} fli_pages, {len(fixtures['planning'])} planning, "
          f"{len(fixtures['location_search'])} location_search, {len(fixtures['location_major'])} location_major cases, "
          f"{out.stat().st_size} bytes")


if __name__ == "__main__":
    main()
