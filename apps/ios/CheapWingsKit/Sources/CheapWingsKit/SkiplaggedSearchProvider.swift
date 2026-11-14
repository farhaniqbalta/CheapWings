import CheapWingsCore
import Foundation

/// One Skiplagged route/date: a parsed page, or an outcome for the runner (retry, stop, failure).
public enum SkiplaggedFetch: Sendable {
    case page(SkiplaggedPage)
    case outcome(ProviderOutcome)
}

/// Skiplagged via its public MCP server — the same request as `providers/skiplagged.py`
/// (personal use; hidden-city and virtual interlining excluded). Parsing and FX are the Rust
/// core's; this type owns the request, pacing and Skiplagged's stop/retry rules.
public struct SkiplaggedSearchProvider: Sendable {
    public let id = "skiplagged"
    /// The web's interval (3 s) and concurrency (C3).
    public let pacing = ProviderPacing(interval: .seconds(3), maxInFlight: 3)
    private let client: MCPClient

    public init(transport: MCPTransport = URLSessionMCPTransport()) {
        client = MCPClient(transport: transport)
    }

    static func arguments(_ combo: RouteDate, request: SearchRequest) -> [String: Any] {
        ["origin": combo.origin, "destination": combo.destination, "departureDate": combo.date,
         "adults": 1, "fareClass": "economy", "limit": 20,
         "includeHiddenCity": false, "includeVirtualInterlining": false, "currency": request.currency]
    }

    public func fetch(_ combo: RouteDate, request: SearchRequest) async -> SkiplaggedFetch {
        let raw: String
        do {
            raw = try await client.callTool(name: "sk_flights_search", arguments: Self.arguments(combo, request: request))
        } catch MCPError.http(let status, let retryAfter) {
            if status == 429 { return .outcome(.retry(after: Self.retryDelay(retryAfter))) }
            if status == 401 || status == 403 { return .outcome(.stop(.blocked("http_\(status)"))) }
            return .outcome(.failed(code: "http_\(status)", hidden: []))
        } catch {
            if Task.isCancelled { return .outcome(.stop(.cancelled)) }
            if let code = (error as? URLError)?.code, OfflineErrors.codes.contains(code) { return .outcome(.stop(.offline)) }
            return .outcome(.failed(code: "network", hidden: []))
        }
        if Task.isCancelled { return .outcome(.stop(.cancelled)) }
        do {
            let payload = try skiplaggedToolPayload(rpcJson: raw)
            return .page(try skiplaggedParse(json: payload, origin: combo.origin, destination: combo.destination,
                                             date: combo.date, displayCurrency: request.currency))
        } catch SkiplaggedError.Failed(let code, _) {
            return .outcome(.failed(code: code, hidden: []))
        } catch {
            return .outcome(.failed(code: "schema_changed", hidden: []))
        }
    }

    /// `rate_limit.retry_after`: seconds, or an HTTP date (time until it), else 60 s.
    static func retryDelay(_ header: String?, now: Date = Date()) -> Duration {
        guard let header = header?.trimmingCharacters(in: .whitespaces), !header.isEmpty else { return .seconds(60) }
        if let seconds = Int(header) { return seconds >= 0 ? .seconds(seconds) : .seconds(60) }
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "en_US_POSIX")
        formatter.timeZone = TimeZone(identifier: "GMT")
        formatter.dateFormat = "EEE, dd MMM yyyy HH:mm:ss zzz"
        guard let date = formatter.date(from: header) else { return .seconds(60) }
        return .seconds(max(0, Int(date.timeIntervalSince(now).rounded(.up))))
    }
}
