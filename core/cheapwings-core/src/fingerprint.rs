//! Itinerary identity, byte-compatible with `compute_fingerprint` in
//! `backend/src/cheapwings/domain/itinerary.py` and `FlightSegment.identity_key`.

use serde::Deserialize;
use sha2::{Digest, Sha256};

/// A wall-clock instant with its UTC offset in seconds (never fabricated).
#[derive(Debug, Clone, PartialEq, Eq, Deserialize)]
pub struct LocalInstant {
    pub y: i32,
    pub mo: u32,
    pub d: u32,
    pub h: u32,
    pub mi: u32,
    pub s: u32,
    pub us: u32,
    pub offset: i32,
}

#[derive(Debug, Clone, PartialEq, Eq, Deserialize)]
pub struct Segment {
    pub ordinal: u32,
    pub marketing: String,
    pub operating: String,
    pub flight: String,
    pub origin: String,
    pub destination: String,
    pub depart: LocalInstant,
    pub arrive: LocalInstant,
}

/// Python `datetime.isoformat()` for an aware datetime: microseconds only when non-zero,
/// offset `±HH:MM`, plus `:SS` only for second-precision offsets.
pub fn isoformat(t: &LocalInstant) -> String {
    let mut out = format!("{:04}-{:02}-{:02}T{:02}:{:02}:{:02}", t.y, t.mo, t.d, t.h, t.mi, t.s);
    if t.us != 0 {
        out += &format!(".{:06}", t.us);
    }
    let sign = if t.offset < 0 { '-' } else { '+' };
    let off = t.offset.unsigned_abs();
    out += &format!("{sign}{:02}:{:02}", off / 3600, off % 3600 / 60);
    if off % 60 != 0 {
        out += &format!(":{:02}", off % 60);
    }
    out
}

/// SHA-256 hex over ordered segment identity fields.
pub fn fingerprint(segments: &[Segment]) -> String {
    let canonical = segments
        .iter()
        .map(|s| {
            [
                s.ordinal.to_string(),
                s.marketing.clone(),
                s.operating.clone(),
                s.flight.clone(),
                s.origin.clone(),
                s.destination.clone(),
                isoformat(&s.depart),
                isoformat(&s.arrive),
            ]
            .join(",")
        })
        .collect::<Vec<_>>()
        .join("|");
    Sha256::digest(canonical.as_bytes()).iter().map(|b| format!("{b:02x}")).collect()
}
