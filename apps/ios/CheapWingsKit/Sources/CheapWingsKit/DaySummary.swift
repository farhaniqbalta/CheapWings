import CheapWingsCore
import Foundation

/// One departure date in the results' date strip: its lowest fare so far and whether every
/// source has searched every route on that date. Pure, so a future Discover screen can reuse it.
public struct DaySummary: Sendable, Identifiable {
    public enum State: Sendable, Equatable {
        case pending
        case searched
        /// Every work item on that date failed (first failure code).
        case failed(String)
    }

    public let date: String  // YYYY-MM-DD
    public let lowest: FoundOffer?
    public let state: State
    /// The date of the overall lowest comparable fare (all tied dates).
    public let isCheapest: Bool
    public var id: String { date }

    /// The day's lowest price in the display currency, for the strip's text and bar; nil when the
    /// day only has offers that could not be converted (never mixed into the strip's scale).
    public var lowestComparable: String? { lowest?.offer.priceComparable }

    /// Set when the day's only offers are in another currency (e.g. "USD"), so the strip labels it.
    public var unconvertedCurrency: String? {
        guard let lowest, lowest.offer.priceComparable == nil else { return nil }
        return lowest.offer.currencyOriginal
    }

    /// `offers` must be ranked (as `SearchSession.offers` is), so each date's first is its lowest.
    public static func make(planned: [WorkItem], finished: Set<WorkItem>, offers: [FoundOffer],
                            failures: [SkippedSearch]) -> [DaySummary] {
        var dates: [String] = []
        for item in planned where !dates.contains(item.routeDate.date) { dates.append(item.routeDate.date) }
        return dates.map { date in
            let items = planned.filter { $0.routeDate.date == date }
            let lowest = offers.first { $0.routeDate.date == date }
            let failed = failures.filter { $0.routeDate.date == date }
            let state: State
            if !items.allSatisfy(finished.contains) {
                state = .pending
            } else if lowest == nil, let first = failed.first, failed.count >= items.count {
                state = .failed(first.code)
            } else {
                state = .searched
            }
            return DaySummary(date: date, lowest: lowest, state: state,
                              isCheapest: lowest.map { isLowest($0, among: offers) } ?? false)
        }
    }

    /// One source over plain route/dates (Fli), as before P5.4.
    public static func make(planned: [RouteDate], finished: Set<RouteDate>, offers: [FoundOffer],
                            failures: [SkippedSearch]) -> [DaySummary] {
        make(planned: planned.map { WorkItem(provider: "fli", routeDate: $0) },
             finished: Set(finished.map { WorkItem(provider: "fli", routeDate: $0) }), offers: offers, failures: failures)
    }

    /// True for every offer tied at the lowest comparable price (exact decimal, same currency).
    /// Offers whose price could not be converted to the display currency are never the lowest.
    /// `offers` must be ranked.
    public static func isLowest(_ offer: FoundOffer, among offers: [FoundOffer]) -> Bool {
        guard let best = offers.first, let bestPrice = best.offer.priceComparable,
              let price = offer.offer.priceComparable, offer.shownPrice.currency == best.shownPrice.currency,
              let a = Decimal(string: price), let b = Decimal(string: bestPrice) else { return false }
        return a == b
    }

    @MainActor
    public static func make(_ session: SearchSession) -> [DaySummary] {
        make(planned: session.planned, finished: session.finished, offers: session.offers, failures: session.failures)
    }
}
