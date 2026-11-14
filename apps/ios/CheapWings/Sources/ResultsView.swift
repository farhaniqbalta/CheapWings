import CheapWingsCore
import CheapWingsKit
import SwiftUI

struct ResultsView: View {
    let model: SearchModel
    private var session: SearchSession { model.session }

    var body: some View {
        List {
            if let info = session.resumable, !session.isRunning {
                // Redraw when the post-block cooldown ends, so Resume enables itself on time.
                TimelineView(.explicit([session.resumeAllowedAfter].compactMap { $0 })) { _ in
                    Section {
                        Text("Unfinished search: \(Self.route(info.request)), \(info.done) of \(info.total) done")
                        if let after = session.resumeAllowedAfter, !session.canResume {
                            Text("Google asked us to slow down — try again after \(after.formatted(date: .omitted, time: .shortened)).")
                                .font(.caption).foregroundStyle(.secondary)
                        }
                        Button("Resume", action: model.resume).disabled(!model.canResume)
                    }
                }
            }
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
                Section {
                    ForEach(session.offers) { found in
                        let info = model.catalog.map { ItineraryInfo.make(offer: found.offer, catalog: $0) }
                        NavigationLink {
                            OfferDetailView(found: found, currency: session.currency, info: info)
                        } label: {
                            OfferRow(found: found, currency: session.currency, info: info)
                        }
                    }
                } header: {
                    Text("Lowest advertised · \(session.offers.count) flights")
                } footer: {
                    if let oldest = session.offers.map(\.fetchedAt).min() {
                        Text("Searched \(oldest, style: .relative) ago")
                    }
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
            if let note = model.historyError ?? session.storeError {
                Section { Text(note).font(.footnote).foregroundStyle(.secondary) }
            }
        }
        .navigationTitle("Results")
        .onChange(of: session.phase) { _, _ in model.progressChanged() }
    }

    static func route(_ request: SearchRequest) -> String {
        "\(request.origins.joined(separator: ","))→\(request.destinations.joined(separator: ","))"
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
        case .backgrounded: return "Paused when the app went to the background."
        case .interrupted: return "Interrupted — the app was closed while searching."
        case .offline: return "Paused: no internet connection. Resume when you are back online."
        }
    }
}

struct OfferRow: View {
    let found: FoundOffer
    let currency: String
    let info: ItineraryInfo?

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack(alignment: .firstTextBaseline) {
                Text(PriceText.display(found.offer.price, currency: found.offer.currency ?? currency))
                    .font(.headline.monospacedDigit())
                Spacer()
                Text(summary).font(.subheadline).foregroundStyle(.secondary)
            }
            Text(found.offer.legs.map(Self.legText).joined(separator: "  ·  "))
                .font(.subheadline)
            if let change = info?.airportChanges.first {
                Label("Change airports \(change.from) → \(change.to)", systemImage: "arrow.left.arrow.right")
                    .font(.caption).foregroundStyle(.orange)
            }
            HStack {
                Text("\(found.routeDate.origin)→\(found.routeDate.destination) · \(found.routeDate.date)")
                Text("Indicative · fees & bags unknown")
            }
            .font(.caption).foregroundStyle(.secondary)
            if found.isStale {
                Text("Older than 1 hour — prices may have changed").font(.caption).foregroundStyle(.orange)
            }
        }
        .padding(.vertical, 2)
    }

    /// "Nonstop · 7h 15m" (duration only when both airports' time zones are known).
    private var summary: String {
        let n = found.offer.legs.count - 1
        let stops = n == 0 ? "Nonstop" : "\(n) stop\(n == 1 ? "" : "s")"
        guard let minutes = info?.totalMinutes else { return stops }
        return "\(stops) · \(ItineraryInfo.durationText(minutes))"
    }

    static func legText(_ leg: FliLeg) -> String {
        "\(leg.airline)\(leg.flightNumber) \(leg.origin)→\(leg.destination) \(leg.departLocal.suffix(5))–\(leg.arriveLocal.suffix(5))"
    }
}
