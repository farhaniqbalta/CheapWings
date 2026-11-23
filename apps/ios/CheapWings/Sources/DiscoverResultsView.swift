import CheapWingsCore
import CheapWingsKit
import SwiftUI

/// P7.6: discovery progress, honest coverage, then one row per shortlisted destination with its
/// provisional discovery price and, once checked, the cheapest checked fare (tap for details).
struct DiscoverResultsView: View {
    let model: SearchModel
    private var session: SearchSession { model.session }

    var body: some View {
        let summary = session.discovery
        let finished = !session.isRunning
        let rows = summary.map { discoverRows(summary: $0, offers: session.offers, currency: session.currency, finished: finished) } ?? []
        List {
            if let info = session.resumable, !session.isRunning {
                Section {
                    Text("Unfinished Discover from \(info.request.origins.joined(separator: ", "))")
                    if !model.network.isOnline {
                        Text("Connect to the internet to resume.").font(.footnote).foregroundStyle(.secondary)
                    }
                    Button("Resume", action: model.resume).disabled(!model.canResume)
                }
            }
            if !session.providerStops.isEmpty {
                Section {
                    ForEach(session.providerStops.keys.sorted(), id: \.self) { provider in
                        if let stop = session.providerStops[provider] {
                            Label(ResultsView.message(for: stop.reason, source: provider), systemImage: "exclamationmark.triangle")
                                .foregroundStyle(Theme.hold)
                        }
                    }
                }
            }
            if let summary {
                Section {
                    Text(progressText(summary))
                    Text(coverageText(summary, rows: rows)).font(.footnote).foregroundStyle(.secondary)
                    if summary.callsFailed > 0 {
                        Text("\(summary.callsFailed) discovery call\(summary.callsFailed == 1 ? "" : "s") failed; destinations from those days may be missing.")
                            .font(.footnote).foregroundStyle(Theme.warn)
                    }
                    if summary.unpriced > 0 {
                        Text("\(summary.unpriced) destinations had no price and were left out.").font(.footnote).foregroundStyle(.secondary)
                    }
                }
            }
            if let outcome = session.emptyOutcome {
                Section { ResultsView.emptyLabel(outcome) }
            }
            if !rows.isEmpty {
                Section {
                    ForEach(rows) { row in
                        if let found = row.checkedOffer {
                            NavigationLink {
                                OfferDetailView(found: found, currency: session.currency,
                                                info: model.catalog.map { ItineraryInfo.make(offer: found.offer, catalog: $0) },
                                                catalog: model.catalog, airlines: model.airlines)
                            } label: { DestinationRow(row: row, currency: session.currency, catalog: model.catalog) }
                        } else {
                            DestinationRow(row: row, currency: session.currency, catalog: model.catalog)
                        }
                    }
                } header: {
                    Text("Destinations, cheapest checked first")
                } footer: {
                    Text("Discovery prices are provisional leads from Skiplagged and may be stale. Checked fares are fresh but indicative; fees and bags are not included.")
                }
            } else if session.phase == .idle {
                ContentUnavailableView("Discover destinations", systemImage: "globe.asia.australia",
                                       description: Text("Choose your airports and dates, then tap Discover."))
            }
            if let note = model.historyError ?? session.storeError {
                Section { Text(note).font(.footnote).foregroundStyle(.secondary) }
            }
        }
        .navigationTitle("Discover")
        .onChange(of: session.phase) { _, _ in model.progressChanged() }
    }

    private func progressText(_ summary: DiscoverySummary) -> String {
        if !summary.committed {
            return session.isRunning ? "Finding destinations: \(summary.callsDone) of \(summary.callsPlanned) calls"
                                     : "Stopped while finding destinations (\(summary.callsDone) of \(summary.callsPlanned) calls)"
        }
        let done = session.finished.count
        return session.isRunning ? "Checking fares: \(done) of \(session.planned.count) checks" : "\(done) of \(session.planned.count) checks done"
    }

    /// "Lowest fares found among N discovered destinations; M checked" (never "cheapest anywhere").
    private func coverageText(_ summary: DiscoverySummary, rows: [DiscoverRow]) -> String {
        let found = Set(summary.leads.map(\.destination)).count
        let checked = Set(session.finished.map(\.routeDate.destination)).count
        return "Lowest fares found among \(found) discovered destination\(found == 1 ? "" : "s"); \(checked) checked. Not every destination was searched."
    }
}

private struct DestinationRow: View {
    let row: DiscoverRow
    let currency: String
    let catalog: LocationCatalog?

    var body: some View {
        HStack(alignment: .firstTextBaseline) {
            VStack(alignment: .leading, spacing: 2) {
                Text(row.destination).codeStyle(.title2)
                Text("\(catalog?.airport(code: row.destination)?.name ?? row.destination) · from \(row.origin) · \(ResultsView.day(row.date))")
                    .font(.caption).foregroundStyle(.secondary).lineLimit(2)
            }
            Spacer()
            VStack(alignment: .trailing, spacing: 2) {
                if let found = row.checkedOffer {
                    Text("Checked fare").font(.caption2).foregroundStyle(.secondary)
                    Text(PriceText.display(found.shownPrice.amount, currency: found.shownPrice.currency))
                        .font(.headline.monospacedDigit())
                } else {
                    Text(row.state == .checking ? "Checking…" : "No checked fare").font(.caption).foregroundStyle(.secondary)
                }
                Text("Discovery price (provisional) \(PriceText.display(row.leadAmount, currency: currency))")
                    .font(.caption2).foregroundStyle(.secondary).italic()
            }
        }
        .accessibilityElement(children: .combine)
    }
}
