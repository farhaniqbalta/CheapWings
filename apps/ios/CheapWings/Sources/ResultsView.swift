import CheapWingsCore
import CheapWingsKit
import SwiftUI

struct ResultsView: View {
    let model: SearchModel

    var body: some View {
        List {
            if case .running(let done, let total) = model.phase {
                Section {
                    ProgressView(value: Double(done), total: Double(max(total, 1))) {
                        Text("Searching \(done) of \(total)")
                    }
                }
            }
            if case .stopped(let reason) = model.phase, let message = Self.message(for: reason) {
                Section { Label(message, systemImage: "exclamationmark.triangle").foregroundStyle(.orange) }
            }
            if model.allFailed {
                Section {
                    Label("No results — Google Flights pages could not be read (page format may have changed).",
                          systemImage: "xmark.octagon").foregroundStyle(.red)
                }
            }
            if !model.offers.isEmpty {
                Section("Lowest advertised · \(model.offers.count) flights") {
                    ForEach(model.offers) { OfferRow(found: $0, currency: model.request.currency) }
                }
            } else if model.phase == .idle {
                ContentUnavailableView("Search one-way fares", systemImage: "airplane",
                                       description: Text("Enter airports and a date range, then search."))
            }
            if !model.failures.isEmpty && !model.allFailed {
                Section("Skipped searches") {
                    ForEach(Array(model.failures.enumerated()), id: \.offset) { _, failure in
                        Text("\(failure.0.origin)→\(failure.0.destination) \(failure.0.date): \(failure.1)")
                            .font(.caption).foregroundStyle(.secondary)
                    }
                }
            }
        }
        .navigationTitle("Results")
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
