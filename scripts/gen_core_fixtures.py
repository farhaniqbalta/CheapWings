"""Generate the shared Rust-core fixtures from the Python reference engine (no network).

Run from repo root: PYTHONPATH=backend/src .venv/bin/python scripts/gen_core_fixtures.py
Writes contracts/fixtures/core/core_fixtures.json with the answers the real Python code
produces. The Rust core, its PyO3 module and its Swift package must all match them exactly.
"""

import json
import random
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

from cheapwings.domain.itinerary import compute_fingerprint
from cheapwings.domain.money import FXSnapshot, Money
from cheapwings.domain.offer import ComparisonStatus, LinkScope, Offer, PriceStatus, ThreeValued
from cheapwings.domain.segments import FlightSegment
from cheapwings.engine.ranking import best_checked_deal, lowest_advertised

rng = random.Random(20261113)
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
                      "expect": outcome(lambda: FXSnapshot("USD", currency, Decimal(rate), "s5", "t")
                                        .convert(Money(Decimal(amount), "USD")).amount)})
        cases.append({"op": "from_minor", "minor": str(minor), "currency": currency,
                      "expect": outcome(lambda: Money.from_minor_units(minor, currency).amount)})
        cases.append({"op": "as_minor", "amount": amount, "currency": currency,
                      "expect": outcome(lambda: Money(Decimal(amount), currency).as_minor_units())})
    for amount, rate, currency in [("0.125", "1", "USD"), ("0.135", "1", "USD"), ("2.5", "1", "IDR"),
                                   ("3.5", "1", "IDR"), ("-0.004", "1", "USD"), ("1250000", "0.0000613", "USD")]:
        cases.append({"op": "fx", "amount": amount, "rate": rate, "currency": currency,
                      "expect": outcome(lambda: FXSnapshot("USD", currency, Decimal(rate), "s5", "t")
                                        .convert(Money(Decimal(amount), "USD")).amount)})
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


fixtures = {"source": "backend/src/cheapwings @ 984cfd2; fli 881aee5", "money": money_cases(1000),
            "fingerprint": fingerprint_cases(500), "ranking": ranking_cases(300),
            "fli_tfs": fli_tfs_cases(50), "fli_pages": fli_page_cases(40)}
out = Path(__file__).resolve().parents[1] / "contracts" / "fixtures" / "core" / "core_fixtures.json"
out.write_text(json.dumps(fixtures, separators=(",", ":")))
print(f"wrote {out.name}: {len(fixtures['money'])} money, {len(fixtures['fingerprint'])} fingerprint, "
      f"{len(fixtures['ranking'])} ranking, {len(fixtures['fli_tfs'])} fli_tfs, "
      f"{len(fixtures['fli_pages'])} fli_pages cases, {out.stat().st_size} bytes")
