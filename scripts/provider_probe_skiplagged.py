"""P0 feasibility probe for the Skiplagged remote MCP server.

Low-volume, terms-compliant probe: connects to the public, unauthenticated
MCP endpoint, lists real tool schemas, and (optionally) performs ONE
one-way flight search for a documented example route/date so the actual
response shape can be captured. Does not hammer the endpoint, does not
attempt to bypass any access control, and does not run in CI.

Usage:
    python scripts/provider_probe_skiplagged.py [--search]

Output: prints tool list/schema to stdout and writes a redacted fixture
to contracts/fixtures/provider/skiplagged_probe_<timestamp>.json
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import importlib.metadata

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client as streamablehttp_client

ENDPOINT = "https://mcp.skiplagged.com/mcp"
FIXTURE_DIR = Path(__file__).resolve().parent.parent / "contracts" / "fixtures" / "provider"

# Example route/date only -- a published non-live example, not a claim about
# a real cheapest fare. Chosen far enough in the future to be a valid search.
EXAMPLE_ORIGIN = "MEL"
EXAMPLE_DEST = "DPS"
EXAMPLE_DATE = "2026-12-16"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


FAQ_QUERIES = [
    "Can I cache or store Skiplagged flight search results returned by the MCP server?",
    "Can a third-party app combine or aggregate Skiplagged results with other flight search providers?",
    "Can I use Skiplagged MCP results in a commercial product?",
    "Does Skiplagged allow redistributing or republishing flight prices from the API or MCP server?",
]


async def run(do_search: bool, do_faq: bool = False) -> dict:
    observed: dict = {
        "provider_id": "skiplagged",
        "endpoint": ENDPOINT,
        "mcp_sdk_version": importlib.metadata.version("mcp"),
        "probe_run_at": _utc_now_iso(),
        "tools": [],
        "search_attempted": False,
        "search_result_sanitized": None,
        "faq_results": [],
        "errors": [],
    }

    try:
        async with streamablehttp_client(ENDPOINT) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                tools_result = await session.list_tools()
                for tool in tools_result.tools:
                    observed["tools"].append(
                        {
                            "name": tool.name,
                            "description": tool.description,
                            "input_schema": tool.input_schema,
                            "output_schema": tool.output_schema,
                        }
                    )

                if do_search:
                    search_tool_name = next(
                        (t.name for t in tools_result.tools if "flights_search" in t.name),
                        None,
                    )
                    if search_tool_name is None:
                        observed["errors"].append(
                            "no flights_search tool found in tools/list result"
                        )
                    else:
                        observed["search_attempted"] = True
                        args = {
                            "origin": EXAMPLE_ORIGIN,
                            "destination": EXAMPLE_DEST,
                            "departureDate": EXAMPLE_DATE,
                            "adults": 1,
                            "fareClass": "economy",
                            "limit": 5,
                            "includeHiddenCity": False,
                            "includeVirtualInterlining": False,
                            "currency": "IDR",
                        }
                        try:
                            result = await session.call_tool(search_tool_name, args)
                            # Store raw content blocks; redact nothing here --
                            # redaction happens before this leaves the probe
                            # script in the committed fixture (see main()).
                            observed["search_tool_name"] = search_tool_name
                            observed["search_args"] = args
                            observed["search_result_sanitized"] = [
                                block.model_dump(mode="json") for block in result.content
                            ]
                            observed["search_structured_content"] = result.structured_content
                            observed["search_is_error"] = result.is_error
                        except Exception as exc:  # noqa: BLE001 - probe script, log and continue
                            observed["errors"].append(f"call_tool failed: {exc!r}")

                if do_faq:
                    faq_tool_name = next(
                        (t.name for t in tools_result.tools if t.name == "sk_faq_search"),
                        None,
                    )
                    if faq_tool_name is None:
                        observed["errors"].append("no sk_faq_search tool found")
                    else:
                        for q in FAQ_QUERIES:
                            try:
                                result = await session.call_tool(
                                    faq_tool_name, {"query": q, "top_k": 3}
                                )
                                observed["faq_results"].append(
                                    {
                                        "query": q,
                                        "content": [
                                            block.model_dump(mode="json")
                                            for block in result.content
                                        ],
                                    }
                                )
                            except Exception as exc:  # noqa: BLE001
                                observed["faq_results"].append(
                                    {"query": q, "error": repr(exc)}
                                )

    except Exception as exc:  # noqa: BLE001 - probe script, record and surface
        observed["errors"].append(f"connection/session failed: {exc!r}")

    return observed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--search",
        action="store_true",
        help="Also perform one low-volume example search call (default: tools/list only).",
    )
    parser.add_argument(
        "--faq",
        action="store_true",
        help="Also query sk_faq_search for published policy answers (caching/aggregation/redistribution).",
    )
    args = parser.parse_args()

    observed = asyncio.run(run(do_search=args.search, do_faq=args.faq))

    print(json.dumps(observed, indent=2, default=str))

    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
    out_path = FIXTURE_DIR / f"skiplagged_probe_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    out_path.write_text(json.dumps(observed, indent=2, default=str))
    print(f"\nWrote fixture: {out_path}", file=sys.stderr)

    return 0 if not observed["errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
