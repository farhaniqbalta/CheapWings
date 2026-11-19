import hashlib

from cheapwings.domain.segments import FlightSegment


def compute_fingerprint(segments: tuple[FlightSegment, ...]) -> str:
    """Stable fingerprint over ordered segment identity fields.

    Only call this when every segment has complete identity-critical fields
    (flight number, carriers, UTC-aware timestamps, airports). Callers with
    missing/ambiguous identity must use IdentityConfidence.INSUFFICIENT_IDENTITY
    and skip fingerprinting rather than forcing a match.
    """
    canonical = "|".join(
        ",".join(str(part) for part in segment.identity_key) for segment in segments
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
