import CheapWingsCore
import CheapWingsKit
import SwiftUI

/// One itinerary: legs with local times and durations, layovers, airport changes, price caveats.
struct OfferDetailView: View {
    let found: FoundOffer
    let currency: String
    let info: ItineraryInfo?

    var body: some View {
        List {
            Section {
                Text(PriceText.display(found.offer.price, currency: found.offer.currency ?? currency))
                    .font(.title2.monospacedDigit())
                Text("Indicative price from Google Flights — fees, baggage and final availability must be checked with the seller.")
                    .font(.caption).foregroundStyle(.secondary)
                if found.isStale {
                    Text("Older than 1 hour — prices may have changed").font(.caption).foregroundStyle(.orange)
                }
                Link("Open this search on Google Flights", destination: found.searchURL)
            }
            Section(header) {
                ForEach(Array(found.offer.legs.enumerated()), id: \.offset) { index, leg in
                    VStack(alignment: .leading, spacing: 2) {
                        Text("\(leg.origin) → \(leg.destination)").font(.headline)
                        Text("\(leg.airline)\(leg.flightNumber)").font(.subheadline)
                        Text("\(Self.time(leg.departLocal)) – \(Self.time(leg.arriveLocal)) local"
                             + (info?.legMinutes[safe: index].flatMap { $0 }.map { " · \(ItineraryInfo.durationText($0))" } ?? ""))
                            .font(.caption).foregroundStyle(.secondary)
                    }
                    if let layover = info?.layovers[safe: index] {
                        layoverRow(layover)
                    }
                }
            }
        }
        .navigationTitle("\(found.routeDate.origin) → \(found.routeDate.destination)")
        .navigationBarTitleDisplayMode(.inline)
    }

    private var header: String {
        let stops = max(found.offer.legs.count - 1, 0)
        var parts = [stops == 0 ? "Nonstop" : "\(stops) stop\(stops == 1 ? "" : "s")", found.routeDate.date]
        if let total = info?.totalMinutes { parts.append("\(ItineraryInfo.durationText(total)) total") }
        return parts.joined(separator: " · ")
    }

    @ViewBuilder private func layoverRow(_ layover: Layover) -> some View {
        let wait = layover.minutes.map { " · \(ItineraryInfo.durationText($0))" } ?? ""
        if let to = layover.toAirport {
            Label("Change airports: \(layover.airport) → \(to)\(wait). Allow time to transfer; not a normal connection.",
                  systemImage: "exclamationmark.triangle")
                .font(.caption).foregroundStyle(.orange)
        } else {
            Label("Layover at \(layover.airport)\(wait)", systemImage: "clock")
                .font(.caption).foregroundStyle(.secondary)
        }
    }

    /// "2026-12-15T06:05" → "Dec 15, 06:05".
    static func time(_ local: String) -> String {
        let parts = local.split(separator: "T")
        guard parts.count == 2, let date = SearchModel.date(String(parts[0])) else { return local }
        return "\(date.formatted(.dateTime.month(.abbreviated).day())), \(parts[1])"
    }
}

extension Array {
    subscript(safe index: Int) -> Element? { indices.contains(index) ? self[index] : nil }
}
