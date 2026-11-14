import CheapWingsCore
import CheapWingsKit
import SwiftUI

/// One itinerary as a vertical timeline: departure, each flight, layovers or airport changes,
/// arrival. Times are local at each airport.
struct OfferDetailView: View {
    let found: FoundOffer
    let currency: String
    let info: ItineraryInfo?
    let catalog: LocationCatalog?
    let airlines: AirlineNames?

    var body: some View {
        List {
            Section {
                VStack(alignment: .leading, spacing: 6) {
                    Text(PriceText.display(found.shownPrice.amount, currency: found.shownPrice.currency))
                        .font(.largeTitle.weight(.bold).monospacedDigit())
                    Text(summary).font(.subheadline).foregroundStyle(.secondary)
                }
                .accessibilityElement(children: .combine)
                .accessibilityAddTraits(.isHeader)
                Link(found.offer.provider == "skiplagged" ? "Open on Skiplagged" : "Open this search on Google Flights",
                     destination: found.searchURL)
                if let note = FxText.note(found.offer, displayCurrency: currency) {
                    Text(note).font(.footnote)
                        .foregroundStyle(found.offer.priceComparable == nil ? AnyShapeStyle(Theme.warn) : AnyShapeStyle(.secondary))
                }
            }
            Section {
                ForEach(Array(steps.enumerated()), id: \.offset) { index, step in
                    StepRow(step: step, isLast: index == steps.count - 1)
                        .listRowSeparator(.hidden)
                }
            }
            Section {
                Text("Indicative price from \(Sources.name(found.offer.provider)), found \(found.fetchedAt.formatted(.relative(presentation: .named))). Fees, baggage and final availability are checked on the seller's site. Times are local at each airport.")
                    .font(.footnote).foregroundStyle(.secondary)
                if found.isStale {
                    Text("Found over an hour ago; the price may have changed.").font(.footnote).foregroundStyle(Theme.warn)
                }
            }
        }
        .navigationTitle("\(found.routeDate.origin) to \(found.routeDate.destination)")
        .navigationBarTitleDisplayMode(.inline)
    }

    private var summary: String {
        let stops = Int(found.offer.stops)
        var parts = [ResultsView.day(found.routeDate.date), stops == 0 ? "nonstop" : "\(stops) stop\(stops == 1 ? "" : "s")"]
        if let total = info?.totalMinutes { parts.append("\(ItineraryInfo.durationText(total)) total") }
        return parts.joined(separator: ", ")
    }

    /// Airports, flights and connections in order.
    private var steps: [Step] {
        let offer = found.offer
        guard !offer.legs.isEmpty else {
            // Skiplagged gives the trip as a whole: departure, a summary, arrival.
            var summary = ["\(Sources.name(offer.provider)) does not list individual flights"]
            if !offer.carriers.isEmpty { summary.append(offer.carriers.joined(separator: " and ")) }
            if let minutes = info?.totalMinutes { summary.append("\(ItineraryInfo.durationText(minutes)) door to door") }
            return [.airport(code: offer.origin, time: offer.departLocal, place: place(offer.origin), endpoint: true),
                    .summary(summary.joined(separator: ". ") + "."),
                    .airport(code: offer.destination, time: offer.arriveLocal, place: place(offer.destination), endpoint: true)]
        }
        var out: [Step] = []
        for (i, leg) in found.offer.legs.enumerated() {
            if i == 0 { out.append(.airport(code: leg.origin, time: leg.departLocal, place: place(leg.origin), endpoint: true)) }
            out.append(.flight(leg, airlines?.name(leg.airline), info?.legMinutes[safe: i] ?? nil))
            let last = i == found.offer.legs.count - 1
            out.append(.airport(code: leg.destination, time: leg.arriveLocal, place: place(leg.destination), endpoint: last))
            if !last, let layover = info?.layovers[safe: i] {
                let next = found.offer.legs[i + 1]
                if let to = layover.toAirport {
                    out.append(.change(from: layover.airport, to: to, minutes: layover.minutes))
                    out.append(.airport(code: next.origin, time: next.departLocal, place: place(next.origin), endpoint: false))
                } else {
                    out.append(.layover(layover.minutes))
                }
            }
        }
        return out
    }

    private func place(_ code: String) -> String { catalog?.airport(code: code)?.name ?? "" }
}

enum Step {
    case airport(code: String, time: String, place: String, endpoint: Bool)
    case flight(FliLeg, String?, Int?)
    case layover(Int?)
    case change(from: String, to: String, minutes: Int?)
    /// A source without individual flights (Skiplagged).
    case summary(String)
}

private struct StepRow: View {
    let step: Step
    let isLast: Bool

    var body: some View {
        HStack(alignment: .top, spacing: 12) {
            Text(timeText)
                .font(.title3.weight(.semibold).monospacedDigit())
                .frame(minWidth: 64, alignment: .trailing)
            rail
            content.frame(maxWidth: .infinity, alignment: .leading).padding(.bottom, 10)
        }
        .accessibilityElement(children: .combine)
    }

    private var timeText: String {
        if case .airport(_, let time, _, _) = step { return String(time.suffix(5)) }
        return ""
    }

    private var isChange: Bool { if case .change = step { return true } else { return false } }

    @ViewBuilder private var rail: some View {
        VStack(spacing: 0) {
            if case .airport(_, _, _, let endpoint) = step {
                Circle()
                    .strokeBorder(.primary, lineWidth: endpoint ? 0 : 2)
                    .background(Circle().fill(endpoint ? AnyShapeStyle(.primary) : AnyShapeStyle(.background)))
                    .frame(width: 12, height: 12)
                    .padding(.top, 7)
            }
            if !isLast {
                Rectangle().fill(isChange ? AnyShapeStyle(Theme.warn) : AnyShapeStyle(.quaternary)).frame(width: 2)
            }
        }
        .frame(width: 14)
        .accessibilityHidden(true)
    }

    @ViewBuilder private var content: some View {
        switch step {
        case .airport(let code, let time, let place, _):
            HStack(alignment: .firstTextBaseline, spacing: 8) {
                Text(code).codeStyle(.title3)
                Text([place, OfferDetailView.dayText(time)].filter { !$0.isEmpty }.joined(separator: ", "))
                    .font(.subheadline).foregroundStyle(.secondary)
            }
        case .flight(let leg, let name, let minutes):
            VStack(alignment: .leading, spacing: 3) {
                CarriersLine(carriers: [AirlineNames.Carrier(code: leg.airline, name: name)], font: .body.weight(.medium))
                Text("\(leg.airline) \(leg.flightNumber)" + (minutes.map { ", \(ItineraryInfo.durationText($0)) in the air" } ?? ""))
                    .font(.subheadline).foregroundStyle(.secondary)
            }
            .padding(.vertical, 2)
        case .layover(let minutes):
            Text("Layover" + (minutes.map { ", \(ItineraryInfo.durationText($0))" } ?? ""))
                .font(.subheadline).foregroundStyle(.secondary)
        case .summary(let text):
            Text(text).font(.subheadline).foregroundStyle(.secondary).padding(.vertical, 2)
        case .change(let from, let to, let minutes):
            VStack(alignment: .leading, spacing: 4) {
                Text("Change airports: \(from) to \(to)" + (minutes.map { ", \(ItineraryInfo.durationText($0))" } ?? ""))
                    .font(.headline).foregroundStyle(Theme.warn)
                Text("You must get yourself to the other airport and through security again. This is not a protected connection.")
                    .font(.subheadline).foregroundStyle(.secondary)
            }
        }
    }
}

extension OfferDetailView {
    /// "2026-12-15T06:05" → "Tue 15 Dec".
    static func dayText(_ local: String) -> String {
        let date = String(local.prefix(10))
        return SearchModel.date(date) == nil ? "" : ResultsView.day(date)
    }
}

extension Array {
    subscript(safe index: Int) -> Element? { indices.contains(index) ? self[index] : nil }
}
