"""S5: generate shared fixtures from the Python reference engine (no network).

Run from repo root: PYTHONPATH=backend/src .venv/bin/python spikes/core-s5/gen_fixtures.py
Writes spikes/core-s5/fixtures.json: money, fingerprint and ranking cases with the answers
the real Python code produces. Rust and Swift cores must match them exactly.
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


fixtures = {"source": "backend/src/cheapwings @ 984cfd2", "money": money_cases(1000),
            "fingerprint": fingerprint_cases(500), "ranking": ranking_cases(300)}
out = Path(__file__).with_name("fixtures.json")
out.write_text(json.dumps(fixtures, separators=(",", ":")))
print(f"wrote {out.name}: {len(fixtures['money'])} money, {len(fixtures['fingerprint'])} fingerprint, "
      f"{len(fixtures['ranking'])} ranking cases, {out.stat().st_size} bytes")
