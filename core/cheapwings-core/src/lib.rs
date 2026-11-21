//! CheapWings shared engine core. Pure logic only: callers do networking and storage.

pub mod discovery;
pub mod fingerprint;
pub mod fli;
pub mod locations;
pub mod money;
pub mod planning;
pub mod ranking;
pub mod skiplagged;

/// Python str.strip also treats the four C0 information separators as whitespace.
pub fn python_strip(text: &str) -> &str {
    text.trim_matches(|c: char| c.is_whitespace() || ('\u{1c}'..='\u{1f}').contains(&c))
}

pub const BUILD_REVISION: &str = env!("CHEAPWINGS_CORE_REVISION");
pub const BUILD_REVISION_C: &str = concat!(env!("CHEAPWINGS_CORE_REVISION"), "\0");
