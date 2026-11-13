import FliProbe
import Foundation

/// S2: the same Fli search as S1, sent by Rust wreq with Chrome 149 TLS/HTTP2 emulation,
/// judged by the same redirect/block/decode/cross-check rules (`FliProbe.evaluate`).
public enum WreqProbe {
    /// Nil when the Chrome-emulating client builds (no network). wreq #1089 failed here on iOS.
    public static func clientBuildError() -> String? { wreqClientBuilds() }

    public static func run(origin: String, destination: String, date: String,
                           currency: String, country: String) async -> ProbeResult {
        let searchURL = Tfs.pageURL(origin: origin, destination: destination, date: date,
                                    currency: currency, country: country)
        var result = ProbeResult(outcome: .networkError, client: "wreq/chrome149", searchURL: searchURL)
        var url = searchURL
        for _ in 0..<3 {  // same bound as providers/fli.py `_get`
            let response: WreqResponse
            do {
                response = try await wreqFetch(url: url.absoluteString)
            } catch {
                result.detail = "\(error)"
                return result
            }
            result.seconds += response.seconds
            result.status = Int(response.status)
            result.httpProtocol = response.httpVersion
            if (300..<400).contains(result.status) {
                guard let location = response.location,
                      let target = URL(string: location, relativeTo: url)?.absoluteURL else {
                    result.outcome = .httpError
                    result.detail = "redirect without location"
                    return result
                }
                guard isAllowedRedirect(target) else {
                    return FliProbe.evaluate(result, blockedRedirect: target, body: Data(), origin: origin,
                                             destination: destination, date: date, currency: currency)
                }
                url = target
                continue
            }
            return FliProbe.evaluate(result, blockedRedirect: nil, body: response.body, origin: origin,
                                     destination: destination, date: date, currency: currency)
        }
        result.outcome = .httpError
        result.detail = "too many redirects"
        return result
    }
}
