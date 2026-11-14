import CheapWingsCore
import Foundation

/// How fast one provider may be called: time between request starts and requests open at once.
public struct ProviderPacing: Sendable, Equatable {
    public let interval: Duration
    public let maxInFlight: Int

    public init(interval: Duration, maxInFlight: Int) {
        self.interval = interval
        self.maxInFlight = max(1, maxInFlight)
    }

    /// Owner-approved after the 270-request live test (docs/log/p5.5-fli-interval.md); the web
    /// measured ~5 in flight at 0.25 s, 6 leaves room for one slow reply.
    public static let fli = ProviderPacing(interval: .milliseconds(250), maxInFlight: 6)
}

/// One route/date's result from any provider.
public enum ProviderOutcome: Sendable {
    /// Offers (possibly none) plus reasons for offers hidden by checks or filters.
    case found(offers: [FoundOffer], hidden: [String])
    /// This route/date could not be searched; the search continues.
    case failed(code: String, hidden: [String])
    /// Stop the whole search (rate limit, block, offline, cancel); this route/date stays pending.
    case stop(StopReason)
}

/// A flight source the iPad engine can pace. Only Fli exists today; Skiplagged/OctoTrip (P5.4)
/// add adapters with their own pacing and stop rules — the runner stays unchanged.
public protocol SearchProvider: Sendable {
    var id: String { get }
    var pacing: ProviderPacing { get }
    /// Never throws: transport errors become `.failed` or `.stop` inside the adapter.
    func search(_ combo: RouteDate, request: SearchRequest) async -> ProviderOutcome
}
