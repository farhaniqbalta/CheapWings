"""Strict adapter-boundary primitives, independent of HTTP and storage."""
import hashlib
import json
from dataclasses import asdict, is_dataclass
from datetime import datetime
from decimal import Decimal

from cheapwings.domain.evidence import ProviderFailure
from cheapwings.domain.money import Money


def decimal_value(value):
    if isinstance(value, bool) or isinstance(value, float) or not isinstance(value, (str, int, Decimal)):
        raise ProviderFailure('invalid_price')
    try:
        result = Decimal(value)
    except Exception as exc:
        raise ProviderFailure('invalid_price') from exc
    if not result.is_finite() or result < 0:
        raise ProviderFailure('invalid_price')
    return result


def money(value, currency):
    if not isinstance(currency, str) or len(currency) != 3 or not currency.isalpha():
        raise ProviderFailure('invalid_currency')
    return Money(decimal_value(value), currency)


def stable_id(*parts):
    return hashlib.sha256(json.dumps(parts, sort_keys=True, default=str).encode()).hexdigest()


def json_payload(text):
    return json.loads(text, parse_float=Decimal)


def obj_dict(value):
    return asdict(value) if is_dataclass(value) else value


def aware_iso(value):
    result = datetime.fromisoformat(value)
    if result.tzinfo is None:
        raise ProviderFailure('missing_segments')
    return result
