"""Provider-neutral shortlist selection. Currency conversion is never inferred here."""
from collections import defaultdict, deque
from decimal import Decimal

from cheapwings.domain.offer import ComparisonStatus, PriceStatus, ThreeValued


def shortlist(candidates, budget, top_count=10):
    """Top prices + 10% competitors; round-robin providers preserve representation.

    Candidates are (row_id, canonical_offer). Unknown-risk advertised candidates may
    be checked, but this does not admit them to the safe normal-ticket ranking.
    """
    eligible = [(key, o) for key, o in candidates if o.provider_quote_handle and
                o.comparable_amount and o.hidden_city != ThreeValued.YES and
                o.comparison_status != ComparisonStatus.INELIGIBLE and
                o.price_status != PriceStatus.CHANGED_OR_UNAVAILABLE]
    eligible.sort(key=lambda pair: (pair[1].comparable_amount.amount, pair[0]))
    if not eligible or budget <= 0:
        return []
    ceiling = eligible[min(top_count, len(eligible))-1][1].comparable_amount.amount * Decimal('1.10')
    buckets = defaultdict(deque)
    providers = set()
    for pair in eligible:
        provider = pair[1].provider_id
        if pair[1].comparable_amount.amount <= ceiling or provider not in providers:
            buckets[provider].append(pair)
        providers.add(provider)
    selected = []
    while buckets and len(selected) < budget:
        for provider in list(buckets):
            selected.append(buckets[provider].popleft()[0])
            if not buckets[provider]:
                del buckets[provider]
            if len(selected) >= budget:
                break
    return selected
