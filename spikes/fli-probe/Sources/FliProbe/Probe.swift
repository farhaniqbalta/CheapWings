import Foundation

/// Which User-Agent the probe sends. TLS is always the platform's own (no impersonation).
public enum UserAgentMode: String, CaseIterable, Sendable {
    case system         // URLSession default (CFNetwork)
    case safariIPad     // iPadOS Safari's default (desktop-class) UA — matches the iPad TLS stack
    case safariIOS      // iPhone Safari
    case chromeDesktop  // what fli-js sends; UA/TLS mismatch

    var header: String? {
        switch self {
        case .system: return nil
        case .safariIPad:
            return "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Safari/605.1.15"
        case .safariIOS:
            return "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1"
        case .chromeDesktop:
            return "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"
        }
    }
}

public enum Outcome: String, Sendable {
    case pass = "PASS"
    case blockedSorry = "BLOCKED_SORRY"        // redirect to google.com/sorry — stop for the day
    case blockedTraffic = "BLOCKED_TRAFFIC"    // "unusual traffic" page — stop for the day
    case blockedRedirect = "BLOCKED_REDIRECT"  // consent or any other off-path redirect — stop
    case rateLimited = "RATE_LIMITED"          // 429 — stop for the day
    case rowless = "ROWLESS"                   // 200 but no ds:1
    case schemaChanged = "SCHEMA_CHANGED"
    case crossCheckFailed = "CROSS_CHECK_FAILED"
    case httpError = "HTTP_ERROR"
    case networkError = "NETWORK_ERROR"

    /// Outcomes after which no further live request may be sent (P5.05 §7 stop rule).
    public var mustStop: Bool { [.blockedSorry, .blockedTraffic, .blockedRedirect, .rateLimited].contains(self) }
}

public struct ProbeResult: Sendable {
    public var outcome: Outcome
    public var status = 0
    public var httpProtocol: String?   // "h2", "h3", "http/1.1"
    public var redirectedTo: String?   // host + path only, never the query
    public var bytes = 0
    public var seconds = 0.0
    public var offers = 0
    public var unpriced = 0
    public var firstOffer: String?
    public var detail = ""
    public var client: String          // e.g. "urlsession/safariIOS", "wreq/chrome149"
    public var searchURL: URL

    public init(outcome: Outcome, client: String, searchURL: URL) {
        self.outcome = outcome
        self.client = client
        self.searchURL = searchURL
    }

    /// One line, no payload — safe to paste into the P5.06 log.
    public var summary: String {
        var parts = ["\(outcome.rawValue)", "client=\(client)", "status=\(status)",
                     "proto=\(httpProtocol ?? "?")", "bytes=\(bytes)", String(format: "t=%.2fs", seconds),
                     "offers=\(offers)", "unpriced=\(unpriced)"]
        if let r = redirectedTo { parts.append("redirect=\(r)") }
        if !detail.isEmpty { parts.append("detail=\(detail)") }
        return parts.joined(separator: " ")
    }
}

/// Redirect rule from `providers/fli.py`: only https www.google.com/travel/flights*, never /unsupported.
public func isAllowedRedirect(_ url: URL) -> Bool {
    url.scheme == "https" && url.host == "www.google.com"
        && url.path.hasPrefix("/travel/flights") && !url.path.hasSuffix("/unsupported")
}

/// One live request. Sends exactly one search (plus at most Google's own same-path redirects).
public final class FliProbe: NSObject, URLSessionTaskDelegate, @unchecked Sendable {
    private var blockedRedirect: URL?
    private var httpProtocol: String?

    public static func run(origin: String, destination: String, date: String,
                           currency: String, country: String, userAgent: UserAgentMode) async -> ProbeResult {
        await FliProbe().run(origin: origin, destination: destination, date: date,
                             currency: currency, country: country, userAgent: userAgent)
    }

    private func run(origin: String, destination: String, date: String,
                     currency: String, country: String, userAgent: UserAgentMode) async -> ProbeResult {
        let url = Tfs.pageURL(origin: origin, destination: destination, date: date, currency: currency, country: country)
        var result = ProbeResult(outcome: .networkError, client: "urlsession/\(userAgent.rawValue)", searchURL: url)
        var request = URLRequest(url: url, timeoutInterval: 25)
        request.setValue("text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", forHTTPHeaderField: "Accept")
        request.setValue("en-US,en;q=0.9", forHTTPHeaderField: "Accept-Language")
        if let ua = userAgent.header { request.setValue(ua, forHTTPHeaderField: "User-Agent") }

        let session = URLSession(configuration: .ephemeral)  // no cookies carried between runs
        defer { session.finishTasksAndInvalidate() }
        let start = Date()
        let data: Data, response: URLResponse
        do {
            (data, response) = try await session.data(for: request, delegate: self)
        } catch {
            result.seconds = Date().timeIntervalSince(start)
            result.detail = "\((error as NSError).domain) \((error as NSError).code)"
            return result
        }
        result.seconds = Date().timeIntervalSince(start)
        result.httpProtocol = httpProtocol
        result.status = (response as? HTTPURLResponse)?.statusCode ?? 0
        return Self.evaluate(result, blockedRedirect: blockedRedirect, body: data, origin: origin,
                             destination: destination, date: date, currency: currency)
    }

    /// Shared verdict for any transport (URLSession here, wreq in S2): `result` carries
    /// status/protocol/timing; `blockedRedirect` is a redirect target the policy refused.
    public static func evaluate(_ result: ProbeResult, blockedRedirect: URL?, body data: Data,
                                origin: String, destination: String, date: String, currency: String) -> ProbeResult {
        var result = result
        result.bytes = data.count
        if let target = blockedRedirect {
            result.redirectedTo = (target.host ?? "?") + target.path
            result.outcome = target.path.hasPrefix("/sorry") ? .blockedSorry : .blockedRedirect
            return result
        }
        if result.status == 429 { result.outcome = .rateLimited; return result }
        guard result.status == 200 else { result.outcome = .httpError; return result }
        guard data.count <= 4_000_000 else { result.outcome = .schemaChanged; result.detail = "body > 4 MB"; return result }

        let html = String(decoding: data, as: UTF8.self)
        if Page.isTrafficBlock(html) { result.outcome = .blockedTraffic; return result }
        guard let payload = Page.extractDs1(html) else { result.outcome = .rowless; return result }
        do {
            let decoded = try Page.decode(payload)
            result.offers = decoded.offers.count
            result.unpriced = decoded.unpriced
            if let first = decoded.offers.first {
                let legs = first.legs.map { "\($0.airline)\($0.flightNumber) \($0.origin)\u{2192}\($0.destination) \($0.departLocal)" }
                result.firstOffer = "\(first.currency ?? "?") \(first.priceText) | " + legs.joined(separator: ", ")
            }
            result.detail = Self.crossCheck(decoded, origin: origin, destination: destination, date: date, currency: currency) ?? ""
            result.outcome = decoded.offers.isEmpty ? .rowless : (result.detail.isEmpty ? .pass : .crossCheckFailed)
        } catch {
            result.outcome = .schemaChanged
            result.detail = "\(error)"
        }
        return result
    }

    /// Nil when every priced offer matches the query (airports, date, currency, positive price).
    static func crossCheck(_ decoded: Decoded, origin: String, destination: String, date: String, currency: String) -> String? {
        for offer in decoded.offers {
            guard let first = offer.legs.first, let last = offer.legs.last else { return "offer without legs" }
            if first.origin != origin || last.destination != destination { return "airports \(first.origin)-\(last.destination)" }
            if !first.departLocal.hasPrefix(date) { return "date \(first.departLocal)" }
            if offer.currency != currency { return "currency \(offer.currency ?? "nil")" }
            if !(offer.price > 0) { return "price \(offer.priceText)" }
            if offer.legs.contains(where: { $0.airline.isEmpty || $0.flightNumber.isEmpty }) { return "missing flight number" }
        }
        return nil
    }

    public func urlSession(_ session: URLSession, task: URLSessionTask,
                           willPerformHTTPRedirection response: HTTPURLResponse, newRequest request: URLRequest,
                           completionHandler: @escaping (URLRequest?) -> Void) {
        if let url = request.url, isAllowedRedirect(url) {
            completionHandler(request)
        } else {
            blockedRedirect = request.url
            completionHandler(nil)  // stop here; never follow to /sorry or consent
        }
    }

    public func urlSession(_ session: URLSession, task: URLSessionTask, didFinishCollecting metrics: URLSessionTaskMetrics) {
        httpProtocol = metrics.transactionMetrics.last?.networkProtocolName
    }
}
