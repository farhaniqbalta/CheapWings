import CheapWingsCore
import Foundation

/// The user's search, as typed. Planning (validation, expansion, the 120 cap) is the Rust core's.
public struct SearchRequest: Sendable, Equatable {
    public var origins: [String]
    public var destinations: [String]
    public var dateFrom: String  // YYYY-MM-DD
    public var dateThrough: String
    public var currency: String
    /// Any / 0 / 1 / 2 stops, applied per offer by the Rust core.
    public var maxStops: UInt32?
    /// Catalog location ids when a side used "Major airports" (for display and persistence).
    public var originMajorIDs: [String]
    public var destinationMajorIDs: [String]

    public static let maxCombinations: UInt32 = 120

    public init(origins: [String], destinations: [String], dateFrom: String, dateThrough: String, currency: String,
                maxStops: UInt32? = nil, originMajorIDs: [String] = [], destinationMajorIDs: [String] = []) {
        self.origins = origins
        self.destinations = destinations
        self.dateFrom = dateFrom
        self.dateThrough = dateThrough
        self.currency = currency
        self.maxStops = maxStops
        self.originMajorIDs = originMajorIDs
        self.destinationMajorIDs = destinationMajorIDs
    }

    /// Point-of-sale country as `providers/fli.py` maps it.
    public var country: String {
        ["IDR": "ID", "USD": "US", "AUD": "AU", "JPY": "JP"][currency] ?? "US"
    }

    public func plan() throws -> [RouteDate] {
        try planSearch(origins: origins, destinations: destinations, dateFrom: dateFrom,
                       dateThrough: dateThrough, maxCombinations: Self.maxCombinations)
    }

    func searchURL(_ combo: RouteDate) -> URL {
        // The core builds a fixed https://www.google.com/... URL from validated codes and dates.
        URL(string: fliSearchUrl(origin: combo.origin, destination: combo.destination, date: combo.date,
                                 currency: currency, country: country))!
    }
}

public struct FoundOffer: Sendable, Identifiable {
    public let id: String
    public let routeDate: RouteDate
    public let offer: FliOffer
    public let searchURL: URL
    public let fetchedAt: Date

    /// Prices older than this are labelled as possibly changed (backend live-data retention: 3600 s).
    public static let staleAfter: TimeInterval = 60 * 60

    public init(routeDate: RouteDate, index: Int, offer: FliOffer, searchURL: URL, fetchedAt: Date = Date()) {
        id = "\(routeDate.origin)-\(routeDate.destination)-\(routeDate.date)-\(index)"
        self.routeDate = routeDate
        self.offer = offer
        self.searchURL = searchURL
        self.fetchedAt = fetchedAt
    }

    public func isStale(at now: Date) -> Bool { now.timeIntervalSince(fetchedAt) > Self.staleAfter }
    public var isStale: Bool { isStale(at: Date()) }
}

public enum StopReason: Sendable, Equatable {
    case finished
    case cancelled
    case rateLimited
    case blocked(String)
    case backgrounded
    /// The app was killed or force-quit while searching (found on next launch).
    case interrupted
}

public enum SearchEvent: Sendable {
    case started(total: Int)
    case progress(done: Int, total: Int)
    case offers([FoundOffer])
    case comboFailed(RouteDate, code: String)
    /// Offers on a usable page that failed the query check (one reason each), so they are
    /// counted instead of silently lost.
    case offersHidden(RouteDate, reasons: [String])
    case stopped(StopReason)
}

/// Runs one Fli search: strictly sequential requests, `interval` between them, stop on any
/// sign of blocking (429, refused redirect, traffic page). Offers are only delivered while
/// the search is still running.
public actor SearchEngine {
    private let transport: FliTransport
    private let interval: Duration
    private let sleep: @Sendable (Duration) async throws -> Void

    public init(transport: FliTransport, interval: Duration = .seconds(1),
                sleep: @escaping @Sendable (Duration) async throws -> Void = { try await Task.sleep(for: $0) }) {
        self.transport = transport
        self.interval = interval
        self.sleep = sleep
    }

    /// Cancelling the consuming task (or dropping the stream) cancels the search.
    public nonisolated func run(_ request: SearchRequest, combos: [RouteDate]) -> AsyncStream<SearchEvent> {
        AsyncStream { continuation in
            let task = Task { await self.execute(request, combos, continuation) }
            continuation.onTermination = { _ in task.cancel() }
        }
    }

    private func execute(_ request: SearchRequest, _ combos: [RouteDate], _ out: AsyncStream<SearchEvent>.Continuation) async {
        func stop(_ reason: StopReason) {
            out.yield(.stopped(reason))
            out.finish()
        }
        out.yield(.started(total: combos.count))
        for (index, combo) in combos.enumerated() {
            if index > 0 {
                do { try await sleep(interval) } catch { return stop(.cancelled) }
            }
            if Task.isCancelled { return stop(.cancelled) }
            let url = request.searchURL(combo)
            let page: FetchedPage
            do {
                page = try await transport.fetch(url)
            } catch {
                if Task.isCancelled { return stop(.cancelled) }
                out.yield(.comboFailed(combo, code: "network"))
                out.yield(.progress(done: index + 1, total: combos.count))
                continue
            }
            if Task.isCancelled { return stop(.cancelled) }  // never deliver after cancel
            if page.status == 429 { return stop(.rateLimited) }
            // providers/fli.py `_deny()`: 401/403 block the provider for good.
            if page.status == 401 || page.status == 403 { return stop(.blocked("http_\(page.status)")) }
            if let refused = page.refusedRedirect { return stop(.blocked((refused.host ?? "?") + refused.path)) }
            if page.status != 200 {
                out.yield(.comboFailed(combo, code: "http_\(page.status)"))
            } else {
                do {
                    let decoded = try fliDecodePage(html: String(decoding: page.body, as: UTF8.self))
                    // Per-offer check: a row Google sends without a currency token must not
                    // discard the page's other offers (P5.2 owner test, CGK→HND).
                    let checked = fliFilterOffers(page: decoded, origin: combo.origin, destination: combo.destination,
                                                  date: combo.date, currency: request.currency, maxStops: request.maxStops)
                    if checked.offers.isEmpty, let reason = checked.rejected.first {
                        out.yield(.comboFailed(combo, code: "cross_check: \(reason)"))
                    } else {
                        if !checked.offers.isEmpty {
                            out.yield(.offers(checked.offers.enumerated().map {
                                FoundOffer(routeDate: combo, index: $0.offset, offer: $0.element, searchURL: url)
                            }))
                        }
                        if !checked.rejected.isEmpty { out.yield(.offersHidden(combo, reasons: checked.rejected)) }
                    }
                } catch FliDecodeError.Failed(let code, _) {
                    if code == "auth_denied" { return stop(.blocked("auth_denied")) }
                    out.yield(.comboFailed(combo, code: code))
                } catch {
                    out.yield(.comboFailed(combo, code: "decode"))
                }
            }
            out.yield(.progress(done: index + 1, total: combos.count))
        }
        stop(.finished)
    }
}

/// Fli prices are indicative (fees, bags, hidden-city unknown), so they rank in the core's
/// "lowest advertised" view — never in "best checked deal".
public func rankLowestAdvertised(_ offers: [FoundOffer]) -> [FoundOffer] {
    let byID = Dictionary(offers.map { ($0.id, $0) }, uniquingKeysWith: { first, _ in first })
    let ranked = lowestAdvertised(groups: [offers.map {
        RankOffer(id: $0.id, priceStatus: "indicative", hiddenCity: "unknown",
                  comparisonStatus: "extra_cost_unknown", amount: $0.offer.price)
    }])
    return ranked.compactMap { byID[$0] }
}
