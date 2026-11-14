import CheapWingsCore
import Foundation

/// One departure date in the results' date strip: its lowest fare so far and whether every
/// route on that date has been searched. Pure, so a future Discover screen can reuse it.
public struct DaySummary: Sendable, Identifiable {
    public enum State: Sendable, Equatable {
        case pending
        case searched
        /// Every route on that date failed (first failure code).
        case failed(String)
    }

    public let date: String  // YYYY-MM-DD
    public let lowest: FoundOffer?
    public let state: State
    /// The date of the overall lowest fare.
    public let isCheapest: Bool
    public var id: String { date }

    /// `offers` must be ranked (as `SearchSession.offers` is), so each date's first is its lowest.
    public static func make(planned: [RouteDate], finished: Set<RouteDate>, offers: [FoundOffer],
                            failures: [SkippedSearch]) -> [DaySummary] {
        var dates: [String] = []
        for combo in planned where !dates.contains(combo.date) { dates.append(combo.date) }
        let cheapestDate = offers.first?.routeDate.date
        return dates.map { date in
            let combos = planned.filter { $0.date == date }
            let lowest = offers.first { $0.routeDate.date == date }
            let failed = failures.filter { $0.routeDate.date == date }
            let state: State
            if !combos.allSatisfy(finished.contains) {
                state = .pending
            } else if lowest == nil, let first = failed.first, failed.count >= combos.count {
                state = .failed(first.code)
            } else {
                state = .searched
            }
            return DaySummary(date: date, lowest: lowest, state: state, isCheapest: date == cheapestDate)
        }
    }

    @MainActor
    public static func make(_ session: SearchSession) -> [DaySummary] {
        make(planned: session.planned, finished: session.finished, offers: session.offers, failures: session.failures)
    }
}
