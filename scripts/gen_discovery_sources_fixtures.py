"""Writes contracts/fixtures/core/discovery_sources_fixtures.json (P7.4).

Anywhere cases wrap the recorded P7.1 probe replies (real prices, utm already redacted) and a few
hand-written replies in a JSON-RPC envelope. Expected observations follow the p7.1 adapter mapping.
Usage: python -I scripts/gen_discovery_sources_fixtures.py
"""

import glob
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FETCHED = "2027-02-20T00:00:00Z"


def rpc(structured=None, text=None, is_error=False):
    result = {"content": [{"type": "text", "text": text if text is not None else "summary"}]}
    if structured is not None:
        result["structuredContent"] = structured
    if is_error:
        result["isError"] = True
    return json.dumps({"jsonrpc": "2.0", "id": 3, "result": result})


def obs(origin, depart, dest, amount, hidden="no", ref=None):
    return {"origin": origin, "destination": dest, "departure_date": depart, "amount": amount,
            "currency": "USD", "source_id": "skiplagged", "observed_at": None, "fetched_at": FETCHED,
            "price_kind": "indicative", "hidden_city": hidden, "source_reference": ref}


def anywhere(name, reply, origin, depart, expect):
    return {"name": name, "rpc_json": reply, "origin": origin, "depart": depart, "fetched_at": FETCHED, "expect": expect}


cases = []
probe = json.loads(Path(glob.glob(str(ROOT / "contracts/fixtures/provider/skiplagged_p71_stage1_*.json"))[0]).read_text())
for call in probe["calls"]:
    if call["tool"] != "sk_destinations_anywhere":
        continue
    s, origin, depart = call["structured"], call["args"]["from"], call["args"]["depart"]
    rows = s["results"]
    first = None
    if rows:
        r = rows[0]
        first = obs(origin, depart, r["destination"]["airport"], str(r["price"]["usdAmount"]), ref=r["deepLink"])
    cases.append(anywhere(f"probe_{origin}_{depart}", rpc(s), origin, depart,
                          {"count": len(rows), "unpriced": 0, "first": first,
                           "fx": [{"currency": "USD", "rate": str(s["pricing"]["rate"])}]}))

link = "https://skiplagged.com/flights/CGK/DPS/2027-03-02"
mixed = {"results": [
    {"type": "DealCard", "destination": {"airport": "DPS"}, "price": {"amount": 1928000.1, "currency": "IDR", "usdAmount": "120.50"},
     "flightType": "Standard", "deepLink": link + "?utm_source=mcp&x=1&utm_medium=ai"},
    {"type": "DealCard", "destination": {"airport": "SIN"}, "price": {"usdAmount": 80}, "flightType": "Hidden City",
     "deepLink": "https://evil.example/flights/CGK/SIN"},
    {"type": "DealCard", "destination": {"airport": "KUL"}, "price": {"amount": 900000}, "flightType": "Standard"},
    {"type": "DealCard", "destination": {"airport": "BKK"}, "price": None, "flightType": "Standard"},
], "pricing": {"rate": 16000.5, "rateAsOf": "2027-02-20T00:00:00Z"}}
cases += [
    anywhere("mixed_rows", rpc(mixed), "CGK", "2027-03-02",
             {"observations": [obs("CGK", "2027-03-02", "DPS", "120.50", ref=link + "?x=1"),
                               obs("CGK", "2027-03-02", "SIN", "80", hidden="unknown")],
              "unpriced": 2, "fx": [{"currency": "USD", "rate": "16000.5"}]}),
    anywhere("text_block_no_rate", rpc(text=json.dumps({"results": [mixed["results"][0] | {"deepLink": link}]})), "CGK", "2027-03-02",
             {"observations": [obs("CGK", "2027-03-02", "DPS", "120.50", ref=link)], "unpriced": 0, "fx": []}),
    anywhere("missing_results", rpc({"pricing": {"rate": 1}}), "CGK", "2027-03-02", {"error": "schema_changed"}),
    anywhere("tool_error", rpc({"results": []}, is_error=True), "CGK", "2027-03-02", {"error": "provider_unavailable"}),
]


def query(origins, f, t):
    return {"origins": origins, "date_from": f, "date_through": t, "display_currency": "IDR", "budget": None, "include_hidden_city": False}


calls = [
    {"name": "one_week", "query": query(["CGK"], "2027-03-01", "2027-03-07"),
     "expect": {"calls": [{"origin": "CGK", "date": f"2027-03-0{d}"} for d in range(1, 8)]}},
    {"name": "two_origins_order", "query": query([" sub", "CGK"], "2027-02-28", "2027-03-01"),
     "expect": {"calls": [{"origin": o, "date": d} for o in ("SUB", "CGK") for d in ("2027-02-28", "2027-03-01")]}},
    {"name": "thirty_one_is_allowed", "query": query(["CGK"], "2027-03-01", "2027-03-31"), "expect": {"count": 31}},
    {"name": "thirty_two_is_too_many", "query": query(["CGK", "SUB"], "2027-03-01", "2027-03-16"), "expect": {"error": "too_many"}},
    {"name": "reversed", "query": query(["CGK"], "2027-03-07", "2027-03-01"), "expect": {"error": "dates_reversed"}},
]
out = ROOT / "contracts/fixtures/core/discovery_sources_fixtures.json"
out.write_text(json.dumps({"_note": "Probe cases hold recorded P7.1 Skiplagged replies; hand cases are fictitious.",
                           "anywhere": cases, "discovery_calls": calls}, indent=2) + "\n")
print(f"wrote {out}: {len(cases)} anywhere, {len(calls)} call cases")
