"""Pinned swoop 0.7 one-way search with strict RPC envelope validation.

Keep the SDK's request builders, decoder and trip construction. Validate before
its None -> successful-empty conversion, without mutating shared SDK globals.
"""

import json
import logging

from cheapwings.domain.evidence import ProviderFailure

logger = logging.getLogger(__name__)


def parse_search_response(text):
    from swoop import rpc

    if len(text) > 4_000_000:
        raise ProviderFailure("partial_payload")
    try:
        frames = json.loads(text.lstrip(")]}'\n\r "))
        if not isinstance(frames, list):
            raise TypeError
        matches = [f for f in frames if isinstance(f, list) and f and f[0] == "wrb.fr"]
        if len(matches) != 1:
            raise ValueError
        frame = matches[0]
        block = frame[5] if len(frame) > 5 else None
        code = block[0] if isinstance(block, list) and block else None
        if type(code) is int and code != 0:
            logger.warning("swoop_search_rpc_failed rpc_status=%d", code)
            if code == 8:
                raise ProviderFailure("http_rate_limited", 120)
            if code in (7, 16):
                raise ProviderFailure("auth_denied")
            raise ProviderFailure("network_timeout" if code == 4 else "provider_unavailable")
        if len(frame) < 3 or not isinstance(frame[2], str):
            raise ValueError
        data = json.loads(frame[2])
        if not isinstance(data, list) or len(data) < 4:
            raise ValueError
    except (ValueError, TypeError, IndexError):
        raise ProviderFailure("schema_changed") from None
    result = rpc._parse_rpc_response(json.dumps([frame]))
    if result is None:
        raise ProviderFailure("schema_changed")
    if any(rpc._safe_get(data, path) for path in ([2, 0], [3, 0])) and not (
        result.best or result.other
    ):
        raise ProviderFailure("schema_changed")
    return result


def search(query, transport):
    from swoop import Passengers, rpc
    from swoop._selection import _build_trip_option
    from swoop.models import SearchResult

    legs = [rpc._normalize_rpc_leg(query.origin, query.destination, str(query.departure_date))]
    passengers = Passengers()
    filters = rpc._build_filters_from_legs(
        legs,
        cabin="economy",
        passengers=passengers,
        sort=rpc.SORT_DEPARTURE_TIME,
        exclude_basic_economy=not query.include_basic_economy,
    )
    response = rpc._http_post(
        rpc.SHOPPING_RPC_URL,
        content=f"f.req={rpc._encode_f_req_payload(filters)}".encode(),
        transport=transport,
    )
    raw = parse_search_response(response.text)
    return SearchResult(
        results=[
            _build_trip_option(
                legs,
                [itinerary],
                cabin="economy",
                passengers=passengers,
                include_basic_economy=query.include_basic_economy,
                sort=rpc.SORT_DEPARTURE_TIME,
            )
            for itinerary in [*raw.best, *raw.other]
        ],
        price_range=raw.price_range,
        is_complete=True,
    )
