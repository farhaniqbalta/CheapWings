import CheapWingsCore
import CheapWingsKit
import SwiftUI

struct ResultsView: View {
    let model: SearchModel
    @State private var selectedDay: String?
    private var session: SearchSession { model.session }

    var body: some View {
        let days = DaySummary.make(session)
        let shown = selectedDay.map { day in session.offers.filter { $0.routeDate.date == day } } ?? session.offers
        List {
            if let info = session.resumable, !session.isRunning {
                // Redraw when the post-block cooldown ends, so Resume enables itself on time.
                TimelineView(.explicit([session.resumeAllowedAfter].compactMap { $0 })) { _ in
                    Section {
                        Text("Unfinished search: \(Self.route(info.request)), \(info.done) of \(info.total) searched")
                        if let after = session.resumeAllowedAfter, !session.canResume {
                            Text("Google asked us to slow down. Try again after \(after.formatted(date: .omitted, time: .shortened)).")
                                .font(.footnote).foregroundStyle(.secondary)
                        } else if !model.network.isOnline {
                            Text("Connect to the internet to resume.").font(.footnote).foregroundStyle(.secondary)
                        }
                        Button("Resume search", action: model.resume).disabled(!model.canResume)
                    }
                }
            }
            if case .stopped(let reason) = session.phase, let message = Self.message(for: reason) {
                Section {
                    Label(message, systemImage: "exclamationmark.triangle")
                        .foregroundStyle(reason.isGoogleStop ? Theme.hold : Theme.warn)
                }
            }
            if !days.isEmpty && (session.isRunning || !session.offers.isEmpty || session.resumable != nil) {
                Section {
                    DateRibbon(days: days, selected: $selectedDay)
                        .listRowInsets(EdgeInsets(top: 8, leading: 12, bottom: 8, trailing: 12))
                        .listRowBackground(Color.clear)
                } header: {
                    HStack {
                        Text(progressText(days))
                        Spacer()
                        if selectedDay != nil {
                            Button("Show all days") { selectedDay = nil }.textCase(nil)
                        }
                    }
                }
            }
            if let outcome = session.emptyOutcome {
                Section { Self.emptyLabel(outcome) }
            }
            if !shown.isEmpty {
                Section {
                    ForEach(shown) { found in
                        let info = model.catalog.map { ItineraryInfo.make(offer: found.offer, catalog: $0) }
                        NavigationLink {
                            OfferDetailView(found: found, currency: session.currency, info: info, catalog: model.catalog, airlines: model.airlines)
                        } label: {
                            OfferRow(found: found, currency: session.currency, info: info,
                                     isCheapest: found.id == session.offers.first?.id, airlines: model.airlines)
                        }
                    }
                } header: {
                    Text("Lowest advertised, \(shown.count) flight\(shown.count == 1 ? "" : "s")")
                } footer: {
                    Text("Indicative prices from Google Flights. Fees and bags are not included.")
                }
            } else if session.phase == .idle {
                ContentUnavailableView("Search one-way fares", systemImage: "airplane",
                                       description: Text("Choose airports and dates, then search."))
            }
            if !session.hiddenOffers.isEmpty {
                Section("Hidden offers") {
                    ForEach(session.hiddenOffers.sorted { $0.key < $1.key }, id: \.key) { reason, count in
                        Text("\(count) offer\(count == 1 ? "" : "s") hidden: \(reason)")
                            .font(.footnote).foregroundStyle(.secondary)
                    }
                }
            }
            if !session.failures.isEmpty {
                Section("Days that could not be searched") {
                    ForEach(Array(session.failures.enumerated()), id: \.offset) { _, failure in
                        Text("\(failure.routeDate.origin) to \(failure.routeDate.destination), \(Self.day(failure.routeDate.date)): \(failure.code)")
                            .font(.footnote).foregroundStyle(.secondary)
                    }
                }
            }
            if let note = model.historyError ?? session.storeError {
                Section { Text(note).font(.footnote).foregroundStyle(.secondary) }
            }
        }
        .navigationTitle("Results")
        .onChange(of: session.phase) { _, _ in model.progressChanged() }
        .onChange(of: session.request) { _, _ in selectedDay = nil }
    }

    private func progressText(_ days: [DaySummary]) -> String {
        let searched = days.filter { $0.state != .pending }.count
        if case .running = session.phase { return "Searching, \(searched) of \(days.count) days done" }
        return "\(searched) of \(days.count) days searched"
    }

    static func route(_ request: SearchRequest) -> String {
        "\(request.origins.joined(separator: ", ")) to \(request.destinations.joined(separator: ", "))"
    }

    /// "2026-12-17" → "Thu 17 Dec".
    static func day(_ ymd: String) -> String {
        SearchModel.date(ymd)?.formatted(.dateTime.weekday(.abbreviated).day().month(.abbreviated)) ?? ymd
    }

    @ViewBuilder
    static func emptyLabel(_ outcome: EmptyOutcome) -> some View {
        switch outcome {
        case .noFlights:
            Label("No flights found for these airports and dates.", systemImage: "airplane.circle")
        case .formatChanged:
            Label("No results: Google Flights pages could not be read (the page format may have changed).",
                  systemImage: "xmark.octagon").foregroundStyle(Theme.hold)
        case .searchesFailed(let count):
            Label("No results: \(count) searches failed. Check the connection and see the list below.",
                  systemImage: "wifi.exclamationmark").foregroundStyle(Theme.hold)
        }
    }

    static func message(for reason: StopReason) -> String? {
        switch reason {
        case .finished: return nil
        case .cancelled: return "Search cancelled."
        case .rateLimited: return "Stopped: Google rate-limited this device. Try again later."
        case .blocked(let detail): return "Stopped: Google blocked automated access (\(detail)). Try again later."
        case .backgrounded: return "Paused when the app went to the background."
        case .interrupted: return "Interrupted: the app was closed while searching."
        case .offline: return "Paused: no internet connection. Resume when you are back online."
        }
    }
}

private extension StopReason {
    var isGoogleStop: Bool {
        switch self {
        case .rateLimited, .blocked: return true
        default: return false
        }
    }
}

/// One flight: price first, codes like airport signs, stops and duration on the right. Reads as one
/// VoiceOver element; stacks vertically at accessibility text sizes.
struct OfferRow: View {
    let found: FoundOffer
    let currency: String
    let info: ItineraryInfo?
    let isCheapest: Bool
    let airlines: AirlineNames?
    @Environment(\.dynamicTypeSize) private var typeSize

    var body: some View {
        let layout = typeSize.isAccessibilitySize
            ? AnyLayout(VStackLayout(alignment: .leading, spacing: 8))
            : AnyLayout(HStackLayout(alignment: .center, spacing: 16))
        layout {
            VStack(alignment: .leading, spacing: 6) {
                Text(price).font(.title3.weight(.bold).monospacedDigit())
                if isCheapest {
                    Text("Cheapest")
                        .font(.caption.weight(.bold))
                        .padding(.horizontal, 8).padding(.vertical, 2)
                        .foregroundStyle(Theme.onSign)
                        .background(Theme.sign, in: RoundedRectangle(cornerRadius: 6))
                }
            }
            .frame(minWidth: typeSize.isAccessibilitySize ? nil : 150, alignment: .leading)

            VStack(alignment: .leading, spacing: 4) {
                ViewThatFits(in: .horizontal) {
                    HStack(alignment: .firstTextBaseline, spacing: 6) { codesLine }
                    VStack(alignment: .leading, spacing: 2) { codesLine }
                }
                Text(detailLine).font(.subheadline).foregroundStyle(.secondary)
                if let change = info?.airportChanges.first {
                    Text("Change airports: \(change.from) to \(change.to)")
                        .font(.subheadline.weight(.semibold)).foregroundStyle(Theme.warn)
                }
                if found.isStale {
                    Text("Found over an hour ago; the price may have changed.")
                        .font(.footnote).foregroundStyle(Theme.warn)
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)

            VStack(alignment: typeSize.isAccessibilitySize ? .leading : .trailing, spacing: 4) {
                Text(stopsText).font(.subheadline)
                if let minutes = info?.totalMinutes {
                    Text(ItineraryInfo.durationText(minutes)).font(.subheadline.monospacedDigit()).foregroundStyle(.secondary)
                }
            }
        }
        .padding(.vertical, 4)
        .accessibilityElement(children: .ignore)
        .accessibilityLabel(spoken)
        .accessibilityHint("Opens flight details")
    }

    @ViewBuilder private var codesLine: some View {
        let first = found.offer.legs.first, last = found.offer.legs.last
        Text(first?.origin ?? found.routeDate.origin).codeStyle()
        Text(Self.time(first?.departLocal)).monospacedDigit()
        Text("to").foregroundStyle(.secondary)
        Text(last?.destination ?? found.routeDate.destination).codeStyle()
        Text(Self.time(last?.arriveLocal)).monospacedDigit()
        if dayShift > 0 {
            Text("+\(dayShift) day").font(.caption).foregroundStyle(.secondary)
        }
    }

    private var flights: String {
        airlines?.flightsText(found.offer.legs)
            ?? found.offer.legs.map { "\($0.airline) \($0.flightNumber)" }.joined(separator: " and ")
    }

    private var price: String { PriceText.display(found.offer.price, currency: found.offer.currency ?? currency) }

    private var stopsText: String {
        let n = max(found.offer.legs.count - 1, 0)
        return n == 0 ? "Nonstop" : "\(n) stop\(n == 1 ? "" : "s")"
    }

    /// "All Nippon Airways NH 856, Thu 17 Dec" or "Singapore Airlines SQ 951 and SQ 632, via SIN, 1h 55m layover, Wed 16 Dec".
    private var detailLine: String {
        var parts = [flights]
        if let layovers = info?.layovers, !layovers.isEmpty {
            parts.append("via " + layovers.map { layover in
                layover.airport + (layover.minutes.map { ", \(ItineraryInfo.durationText($0)) layover" } ?? "")
            }.joined(separator: "; "))
        }
        parts.append(ResultsView.day(found.routeDate.date))
        return parts.joined(separator: ", ")
    }

    private var dayShift: Int {
        guard let dep = found.offer.legs.first?.departLocal.prefix(10), let arr = found.offer.legs.last?.arriveLocal.prefix(10),
              let a = SearchModel.date(String(dep)), let b = SearchModel.date(String(arr)) else { return 0 }
        return Calendar(identifier: .gregorian).dateComponents([.day], from: a, to: b).day ?? 0
    }

    private var spoken: String {
        let first = found.offer.legs.first, last = found.offer.legs.last
        let route = "\(first?.origin ?? "") \(Self.time(first?.departLocal)) to \(last?.destination ?? "") \(Self.time(last?.arriveLocal))"
            + (dayShift > 0 ? ", next day" : "")
        var parts = [price, isCheapest ? "cheapest" : nil, stopsText,
                     info?.totalMinutes.map { ItineraryInfo.spokenDuration($0) },
                     route, flights, ResultsView.day(found.routeDate.date)].compactMap { $0 }
        if let change = info?.airportChanges.first { parts.append("change airports from \(change.from) to \(change.to)") }
        if found.isStale { parts.append("found over an hour ago") }
        parts.append("indicative price")
        return parts.joined(separator: ", ")
    }

    static func time(_ local: String?) -> String { local.map { String($0.suffix(5)) } ?? "" }
}
