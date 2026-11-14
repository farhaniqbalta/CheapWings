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
    /// The device lost its internet connection; unfinished route/dates stay pending.
    case offline
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

/// Runs one search over a list of route/dates with one provider (Fli today), paced by the
/// provider's own `ProviderPacing` (start-to-start, several in flight, results in plan order),
/// stopping on any sign of blocking or a lost connection. Offers are only delivered while the
/// search is still running.
public actor SearchEngine {
    /// Hidden-offer reason for itineraries over the user's Max stops.
    public static let stopLimitReason = "more stops than your Max stops"

    private let provider: SearchProvider
    private let sleep: @Sendable (Duration) async throws -> Void

    public init(provider: SearchProvider,
                sleep: @escaping @Sendable (Duration) async throws -> Void = { try await Task.sleep(for: $0) }) {
        self.provider = provider
        self.sleep = sleep
    }

    /// Fli with explicit pacing (tests use `maxInFlight: 1` for the one-at-a-time engine).
    public init(transport: FliTransport, interval: Duration = ProviderPacing.fli.interval,
                maxInFlight: Int = ProviderPacing.fli.maxInFlight,
                sleep: @escaping @Sendable (Duration) async throws -> Void = { try await Task.sleep(for: $0) }) {
        self.init(provider: FliSearchProvider(transport: transport, pacing: ProviderPacing(interval: interval, maxInFlight: maxInFlight)),
                  sleep: sleep)
    }

    /// Cancelling the consuming task (or dropping the stream) cancels the search.
    public nonisolated func run(_ request: SearchRequest, combos: [RouteDate]) -> AsyncStream<SearchEvent> {
        AsyncStream { continuation in
            let task = Task { [provider, sleep] in
                await PacedRunner.execute(provider: provider, request: request, combos: combos, sleep: sleep, out: continuation)
            }
            continuation.onTermination = { _ in task.cancel() }
        }
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
