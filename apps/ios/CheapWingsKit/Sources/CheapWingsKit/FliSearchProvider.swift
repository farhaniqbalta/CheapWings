import CheapWingsCore
import Foundation

/// Google Flights via Fli: the only provider on the iPad today. All Google-specific rules live
/// here (moved unchanged from the P5.6 engine), so the runner knows nothing about Fli.
public struct FliSearchProvider: SearchProvider {
    public let id = "fli"
    public let pacing: ProviderPacing
    private let transport: FliTransport

    /// Pause (Resume later) rather than fail: a wrong "failed" loses that route/date for good.
    /// Includes DNS/host errors from Wi-Fi with no internet (captive portal, dead router).
    static let offlineCodes: Set<URLError.Code> = [.notConnectedToInternet, .networkConnectionLost,
                                                   .dataNotAllowed, .internationalRoamingOff,
                                                   .cannotFindHost, .dnsLookupFailed, .cannotConnectToHost]

    public init(transport: FliTransport, pacing: ProviderPacing = .fli) {
        self.transport = transport
        self.pacing = pacing
    }

    public func search(_ combo: RouteDate, request: SearchRequest) async -> ProviderOutcome {
        let url = request.searchURL(combo)
        let page: FetchedPage
        do {
            page = try await transport.fetch(url)
        } catch {
            if Task.isCancelled { return .stop(.cancelled) }
            if let code = (error as? URLError)?.code, Self.offlineCodes.contains(code) { return .stop(.offline) }
            return .failed(code: "network", hidden: [])
        }
        if Task.isCancelled { return .stop(.cancelled) }
        if page.status == 429 { return .stop(.rateLimited) }
        // providers/fli.py `_deny()`: 401/403 block the provider for good.
        if page.status == 401 || page.status == 403 { return .stop(.blocked("http_\(page.status)")) }
        if let refused = page.refusedRedirect { return .stop(.blocked((refused.host ?? "?") + refused.path)) }
        if page.status != 200 { return .failed(code: "http_\(page.status)", hidden: []) }
        do {
            let decoded = try fliDecodePage(html: String(decoding: page.body, as: UTF8.self))
            // Per-offer check: a row Google sends without a currency token must not discard the
            // page's other offers (P5.2 owner test, CGK→HND).
            let checked = fliFilterOffers(page: decoded, origin: combo.origin, destination: combo.destination,
                                          date: combo.date, currency: request.currency, maxStops: request.maxStops)
            // Failed only when bad data removed everything; Max stops alone is a normal result.
            if checked.offers.isEmpty, checked.excludedByStops == 0, let reason = checked.rejected.first {
                return .failed(code: "cross_check: \(reason)", hidden: [])
            }
            let offers = checked.offers.enumerated().map {
                FoundOffer(routeDate: combo, index: $0.offset, offer: $0.element, searchURL: url)
            }
            let hidden = checked.rejected + Array(repeating: SearchEngine.stopLimitReason, count: Int(checked.excludedByStops))
            return .found(offers: offers, hidden: hidden)
        } catch FliDecodeError.Failed(let code, _) {
            return code == "auth_denied" ? .stop(.blocked("auth_denied")) : .failed(code: code, hidden: [])
        } catch {
            return .failed(code: "decode", hidden: [])
        }
    }
}
