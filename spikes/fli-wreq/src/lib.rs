//! One GET through wreq's Chrome emulation (BoringSSL TLS + HTTP/2 fingerprint).
//! Redirects are never followed here; Swift applies CheapWings' redirect policy.

use std::time::{Duration, Instant};

uniffi::setup_scaffolding!();

#[derive(uniffi::Record)]
pub struct WreqResponse {
    pub status: u16,
    pub location: Option<String>,
    pub http_version: String,
    pub body: Vec<u8>,
    pub seconds: f64,
}

#[derive(Debug, thiserror::Error, uniffi::Error)]
pub enum WreqError {
    #[error("client build failed: {0}")]
    Build(String),
    #[error("request failed: {0}")]
    Request(String),
    #[error("body larger than 4 MB")]
    TooLarge,
}

const MAX_BODY: usize = 4_000_000;

#[uniffi::export(async_runtime = "tokio")]
pub async fn wreq_fetch(url: String) -> Result<WreqResponse, WreqError> {
    let client = wreq::Client::builder()
        .emulation(wreq_util::Emulation::Chrome149)
        .redirect(wreq::redirect::Policy::none())
        .timeout(Duration::from_secs(25))
        .build()
        .map_err(|e| WreqError::Build(format!("{e:?}")))?;
    let start = Instant::now();
    let response = client
        .get(url)
        .header("accept-language", "en-US,en;q=0.9")
        .send()
        .await
        .map_err(|e| WreqError::Request(format!("{e:?}")))?;
    let status = response.status().as_u16();
    let http_version = format!("{:?}", response.version());
    let location = response
        .headers()
        .get("location")
        .and_then(|v| v.to_str().ok())
        .map(str::to_owned);
    let body = response.bytes().await.map_err(|e| WreqError::Request(format!("{e:?}")))?;
    if body.len() > MAX_BODY {
        return Err(WreqError::TooLarge);
    }
    Ok(WreqResponse { status, location, http_version, body: body.to_vec(), seconds: start.elapsed().as_secs_f64() })
}

/// Builds the Chrome-emulating client without any network I/O. On iOS this is where
/// wreq issue #1089 failed (`boring tls error: ErrorStack([])`), so it is checked separately.
#[uniffi::export]
pub fn wreq_client_builds() -> Option<String> {
    wreq::Client::builder()
        .emulation(wreq_util::Emulation::Chrome149)
        .build()
        .err()
        .map(|e| format!("{e:?}"))
}

#[cfg(test)]
mod tests {
    #[test]
    fn client_builds_on_host() {
        assert_eq!(super::wreq_client_builds(), None);
    }
}
