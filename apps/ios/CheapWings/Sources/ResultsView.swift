import CheapWingsCore
import CheapWingsKit
import SwiftUI

struct ResultsView: View {
    let session: SearchSession

    var body: some View {
        List {
            if case .running(let done, let total) = session.phase {
                Section {
                    ProgressView(value: Double(done), total: Double(max(total, 1))) {
                        Text("Searching \(done) of \(total)")
                    }
                }
            }
            if case .stopped(let reason) = session.phase, let message = Self.message(for: reason) {
                Section { Label(message, systemImage: "exclamationmark.triangle").foregroundStyle(.orange) }
            }
            if let outcome = session.emptyOutcome {
                Section { Self.emptyLabel(outcome) }
            }
            if !session.offers.isEmpty {
                Section("Lowest advertised · \(session.offers.count) flights") {
                    ForEach(session.offers) { OfferRow(found: $0, currency: session.currency) }
                }
            } else if session.phase == .idle {
                ContentUnavailableView("Search one-way fares", systemImage: "airplane",
                                       description: Text("Enter airports and a date range, then search."))
            }
            if !session.hiddenOffers.isEmpty {
                Section("Hidden offers") {
                    ForEach(session.hiddenOffers.sorted { $0.key < $1.key }, id: \.key) { reason, count in
                        Text("\(count) offer\(count == 1 ? "" : "s") hidden: \(reason)")
                            .font(.caption).foregroundStyle(.secondary)
                    }
                }
            }
            if !session.failures.isEmpty {
                Section("Skipped searches") {
                    ForEach(Array(session.failures.enumerated()), id: \.offset) { _, failure in
                        Text("\(failure.routeDate.origin)→\(failure.routeDate.destination) \(failure.routeDate.date): \(failure.code)")
                            .font(.caption).foregroundStyle(.secondary)
                    }
                }
            }
        }
        .navigationTitle("Results")
    }

    @ViewBuilder
    static func emptyLabel(_ outcome: EmptyOutcome) -> some View {
        switch outcome {
        case .noFlights:
            Label("No flights found for these routes and dates.", systemImage: "airplane.circle")
        case .formatChanged:
            Label("No results — Google Flights pages could not be read (page format may have changed).",
                  systemImage: "xmark.octagon").foregroundStyle(.red)
        case .searchesFailed(let count):
            Label("No results — \(count) searches failed. Check the connection and see the list below.",
                  systemImage: "wifi.exclamationmark").foregroundStyle(.red)
        }
    }

    static func message(for reason: StopReason) -> String? {
        switch reason {
        case .finished: return nil
        case .cancelled: return "Search cancelled."
        case .rateLimited: return "Stopped: Google rate-limited this device. Try again later."
        case .blocked(let detail): return "Stopped: Google blocked automated access (\(detail)). Try again later."
        case .backgrounded: return "Paused when the app went to the background. Search again to continue."
        }
    }
}

struct OfferRow: View {
    let found: FoundOffer
    let currency: String

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack(alignment: .firstTextBaseline) {
                Text(PriceText.display(found.offer.price, currency: found.offer.currency ?? currency))
                    .font(.headline.monospacedDigit())
                Spacer()
                Text(stops).font(.subheadline).foregroundStyle(.secondary)
            }
            Text(found.offer.legs.map(Self.legText).joined(separator: "  ·  "))
                .font(.subheadline)
            HStack {
                Text("\(found.routeDate.origin)→\(found.routeDate.destination) · \(found.routeDate.date)")
                Text("Indicative · fees & bags unknown")
            }
            .font(.caption).foregroundStyle(.secondary)
            Link("Open on Google Flights", destination: found.searchURL).font(.caption)
        }
        .padding(.vertical, 2)
    }

    private var stops: String {
        let n = found.offer.legs.count - 1
        return n == 0 ? "Nonstop" : "\(n) stop\(n == 1 ? "" : "s")"
    }

    static func legText(_ leg: FliLeg) -> String {
        "\(leg.airline)\(leg.flightNumber) \(leg.origin)→\(leg.destination) \(leg.departLocal.suffix(5))–\(leg.arriveLocal.suffix(5))"
    }
}
