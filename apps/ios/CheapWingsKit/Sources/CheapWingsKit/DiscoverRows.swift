import CheapWingsCore
import Foundation

/// One shortlisted destination on the Discover screen: the provisional discovery price and, once a
/// check came back, the cheapest checked fare for that exact route and date.
public struct DiscoverRow: Identifiable, Sendable {
    public enum State: Sendable, Equatable { case checked, checking, noFare }

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
public func discoverRows(summary: DiscoverySummary, offers: [FoundOffer], currency: String, finished: Bool) -> [DiscoverRow] {
    let rows = summary.selected.map { lead -> DiscoverRow in
        let best = offers
            .filter { $0.routeDate.origin == lead.origin && $0.routeDate.destination == lead.destination && $0.routeDate.date == lead.date }
            .filter { $0.offer.priceComparable != nil && $0.shownPrice.currency == currency }
            .min { (decimal($0.offer.priceComparable!) ?? .greatestFiniteMagnitude) < (decimal($1.offer.priceComparable!) ?? .greatestFiniteMagnitude) }
        return DiscoverRow(origin: lead.origin, destination: lead.destination, date: lead.date, leadAmount: lead.comparableAmount,
                           checkedOffer: best, state: best != nil ? .checked : finished ? .noFare : .checking)
    }
    let amount = { (text: String) in decimal(text) ?? .greatestFiniteMagnitude }
    let checked = rows.filter { $0.checkedOffer != nil }
        .sorted { amount($0.checkedOffer!.offer.priceComparable!) < amount($1.checkedOffer!.offer.priceComparable!) }
    let rest = rows.filter { $0.checkedOffer == nil }.sorted { amount($0.leadAmount) < amount($1.leadAmount) }
    return checked + rest
}
