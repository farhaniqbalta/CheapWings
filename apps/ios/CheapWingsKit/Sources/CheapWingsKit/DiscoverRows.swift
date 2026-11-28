import CheapWingsCore
import Foundation

/// One shortlisted destination on the Discover screen: the provisional discovery price and, once a
/// check came back, the cheapest checked fare for that exact route and date.
public struct DiscoverRow: Identifiable, Sendable {
    public enum State: Sendable, Equatable { case checked, checking, noFare, checkFailed }

    public let origin: String
    public let destination: String
    public let date: String
    /// Discovery price in the display currency: a provisional lead, never a checked fare.
    public let leadAmount: String
    public let checkedOffer: FoundOffer?
    public let state: State

    public var id: String { "\(origin)-\(destination)-\(date)" }
}

private func decimal(_ text: String) -> Decimal? { Decimal(string: text, locale: Locale(identifier: "en_US_POSIX")) }

/// Rows for the shortlist; checked fares first (by checked price), then leads by discovery price.
public func discoverRows(summary: DiscoverySummary, offers: [FoundOffer], currency: String, finished: Bool,
                         failed: Set<RouteDate> = []) -> [DiscoverRow] {
    let rows = summary.selected.map { lead -> DiscoverRow in
        let best = offers
            .filter { $0.routeDate.origin == lead.origin && $0.routeDate.destination == lead.destination && $0.routeDate.date == lead.date }
            .filter { $0.offer.priceComparable != nil && $0.shownPrice.currency == currency }
            .min { (decimal($0.offer.priceComparable!) ?? .greatestFiniteMagnitude) < (decimal($1.offer.priceComparable!) ?? .greatestFiniteMagnitude) }
        return DiscoverRow(origin: lead.origin, destination: lead.destination, date: lead.date, leadAmount: lead.comparableAmount,
                           checkedOffer: best,
                           state: best != nil ? .checked
                               : failed.contains(RouteDate(origin: lead.origin, destination: lead.destination, date: lead.date)) ? .checkFailed
                               : finished ? .noFare : .checking)
    }
    let amount = { (text: String) in decimal(text) ?? .greatestFiniteMagnitude }
    let checked = rows.filter { $0.checkedOffer != nil }
        .sorted { amount($0.checkedOffer!.offer.priceComparable!) < amount($1.checkedOffer!.offer.priceComparable!) }
    let rest = rows.filter { $0.checkedOffer == nil }.sorted { amount($0.leadAmount) < amount($1.leadAmount) }
    return checked + rest
}

/// "Lowest fares found among `found` discovered destinations; `checked` checked." Only after the
/// snapshot is committed; a destination counts as checked when one of its checks succeeded.
public func discoverCoverage(summary: DiscoverySummary, finished: Set<WorkItem>, failures: [SkippedSearch]) -> (found: Int, checked: Int)? {
    guard summary.committed else { return nil }
    let failed = Set(failures.map { WorkItem(provider: $0.provider, routeDate: $0.routeDate) })
    let checked = Set(finished.subtracting(failed).map(\.routeDate.destination))
    return (Set(summary.leads.map(\.destination)).count, checked.count)
}

/// Checks that failed: finished with a failure, or never run because their source stopped us
/// (the runner leaves a stopped lane's later items unfinished). Unique work items, not events.
private func failedChecks(planned: [WorkItem], finished: Set<WorkItem>, failures: [SkippedSearch],
                          stopped: Set<String>) -> Set<WorkItem> {
    let failed = Set(failures.map { WorkItem(provider: $0.provider, routeDate: $0.routeDate) })
    return Set(planned.filter { item in
        finished.contains(item) ? failed.contains(item) : stopped.contains(item.provider)
    })
}

/// Route/dates where every planned check failed (no source answered for them).
public func failedRouteDates(planned: [WorkItem], finished: Set<WorkItem>, failures: [SkippedSearch],
                             stopped: Set<String> = []) -> Set<RouteDate> {
    let bad = failedChecks(planned: planned, finished: finished, failures: failures, stopped: stopped)
    return Set(Dictionary(grouping: planned, by: \.routeDate).filter { _, items in items.allSatisfy(bad.contains) }.keys)
}

/// The failed-check count shown on the Discover screen (matches the web's count of failed work items).
public func failedCheckCount(planned: [WorkItem], finished: Set<WorkItem>, failures: [SkippedSearch],
                             stopped: Set<String> = []) -> Int {
    failedChecks(planned: planned, finished: finished, failures: failures, stopped: stopped).count
}
