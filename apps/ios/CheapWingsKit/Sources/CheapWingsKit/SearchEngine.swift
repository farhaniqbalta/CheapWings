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
    /// Sources to search (P5.4): "fli", "skiplagged".
    public var providers: [String]

    public static let maxCombinations: UInt32 = 120

    public init(origins: [String], destinations: [String], dateFrom: String, dateThrough: String, currency: String,
                maxStops: UInt32? = nil, originMajorIDs: [String] = [], destinationMajorIDs: [String] = [],
                providers: [String] = ["fli"]) {
        self.origins = origins
        self.destinations = destinations
        self.dateFrom = dateFrom
        self.dateThrough = dateThrough
        self.currency = currency
        self.maxStops = maxStops
        self.originMajorIDs = originMajorIDs
        self.destinationMajorIDs = destinationMajorIDs
        self.providers = providers.isEmpty ? ["fli"] : providers
    }

    /// Point-of-sale country as `providers/fli.py` maps it.
    public var country: String {
        ["IDR": "ID", "USD": "US", "AUD": "AU", "JPY": "JP"][currency] ?? "US"
    }

    public func plan() throws -> [RouteDate] {
        try planSearch(origins: origins, destinations: destinations, dateFrom: dateFrom,
                       dateThrough: dateThrough, maxCombinations: Self.maxCombinations)
    }

    /// Work items for a plan: every selected source for every route/date, date order first.
    public func items(_ combos: [RouteDate]) -> [WorkItem] {
        combos.flatMap { combo in providers.map { WorkItem(provider: $0, routeDate: combo) } }
    }

    func searchURL(_ combo: RouteDate) -> URL {
        // The core builds a fixed https://www.google.com/... URL from validated codes and dates.
        URL(string: fliSearchUrl(origin: combo.origin, destination: combo.destination, date: combo.date,
                                 currency: currency, country: country))!
    }

    /// Where an offer's "open on the source" link points.
    func sourceURL(_ combo: RouteDate, offer: SourceOffer) -> URL {
        if offer.provider == "skiplagged" {
            return offer.link.flatMap(URL.init(string:))
                ?? URL(string: "https://skiplagged.com/flights/\(combo.origin)/\(combo.destination)/\(combo.date)")!
        }
        return searchURL(combo)
    }
}

public struct FoundOffer: Sendable, Identifiable {
    public let id: String
    public let routeDate: RouteDate
    public let offer: SourceOffer
    public let searchURL: URL
    public let fetchedAt: Date

    /// Prices older than this are labelled as possibly changed (backend live-data retention: 3600 s).
    public static let staleAfter: TimeInterval = 60 * 60

    public init(routeDate: RouteDate, index: Int, offer: SourceOffer, searchURL: URL, fetchedAt: Date = Date()) {
        id = "\(offer.provider)-\(routeDate.origin)-\(routeDate.destination)-\(routeDate.date)-\(index)"
        self.routeDate = routeDate
        self.offer = offer
        self.searchURL = searchURL
        self.fetchedAt = fetchedAt
    }

    public var providerID: String { offer.provider }

    /// The price to show: the comparable (display-currency) amount, else the original price.
    public var shownPrice: (amount: String, currency: String) {
        if let comparable = offer.priceComparable {
            return (comparable, offer.fx?.toCurrency ?? offer.currencyOriginal)
        }
        return (offer.priceOriginal, offer.currencyOriginal)
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
    /// Precedes one finished work item's events (index into the items the run was given);
    /// that item's offers/hidden/failure and its `.progress` follow without interleaving.
    case item(Int)
    case progress(done: Int, total: Int)
    case offers([FoundOffer])
    case comboFailed(RouteDate, code: String)
    /// Offers on a usable page that failed the query check (one reason each), so they are
    /// counted instead of silently lost.
    case offersHidden(RouteDate, reasons: [String])
    /// One source stopped on its own (rate limit, block); other sources keep going.
    case providerStopped(String, StopReason)
    case stopped(StopReason)
}

/// Runs one search over work items (provider × route/date): one paced lane per provider, side by
/// side, each with its own `ProviderPacing`, stop rules and retry-after. Offers are only
/// delivered while the search is still running.
public actor SearchEngine {
    /// Hidden-offer reason for itineraries over the user's Max stops.
    public static let stopLimitReason = "more stops than your Max stops"

    private let providers: [SearchProvider]
    private let sleep: @Sendable (Duration) async throws -> Void

    public init(providers: [SearchProvider],
                sleep: @escaping @Sendable (Duration) async throws -> Void = { try await Task.sleep(for: $0) }) {
        self.providers = providers
        self.sleep = sleep
    }

    public init(provider: SearchProvider,
                sleep: @escaping @Sendable (Duration) async throws -> Void = { try await Task.sleep(for: $0) }) {
        self.init(providers: [provider], sleep: sleep)
    }

    /// Fli with explicit pacing (tests use `maxInFlight: 1` for the one-at-a-time engine).
    public init(transport: FliTransport, interval: Duration = ProviderPacing.fli.interval,
                maxInFlight: Int = ProviderPacing.fli.maxInFlight,
                sleep: @escaping @Sendable (Duration) async throws -> Void = { try await Task.sleep(for: $0) }) {
        self.init(provider: FliSearchProvider(transport: transport, pacing: ProviderPacing(interval: interval, maxInFlight: maxInFlight)),
                  sleep: sleep)
    }

    /// One provider (the first) over these route/dates.
    public nonisolated func run(_ request: SearchRequest, combos: [RouteDate]) -> AsyncStream<SearchEvent> {
        let provider = providers.first?.id ?? "fli"
        return run(request, items: combos.map { WorkItem(provider: provider, routeDate: $0) })
    }

    /// Cancelling the consuming task (or dropping the stream) cancels the search.
    public nonisolated func run(_ request: SearchRequest, items: [WorkItem]) -> AsyncStream<SearchEvent> {
        AsyncStream { continuation in
            let task = Task { [providers, sleep] in
                await PacedRunner.execute(providers: providers, request: request, items: items, sleep: sleep, out: continuation)
            }
            continuation.onTermination = { _ in task.cancel() }
        }
    }
}

/// Every source's prices are indicative, so they rank in the core's "lowest advertised" view.
/// Offers whose price could not be converted to the display currency rank after the rest.
public func rankLowestAdvertised(_ offers: [FoundOffer]) -> [FoundOffer] {
    let byID = Dictionary(offers.map { ($0.id, $0) }, uniquingKeysWith: { first, _ in first })
    let ranked = lowestAdvertised(groups: [offers.map {
        RankOffer(id: $0.id, priceStatus: "indicative", hiddenCity: $0.offer.hiddenCity,
                  comparisonStatus: $0.offer.priceComparable == nil ? "currency_unresolved" : "extra_cost_unknown",
                  amount: $0.offer.priceComparable)
    }])
    let rankedIDs = Set(ranked)
    // The core leaves out offers it cannot compare; keep them, after the ranked ones.
    return ranked.compactMap { byID[$0] } + offers.filter { !rankedIDs.contains($0.id) }
}
