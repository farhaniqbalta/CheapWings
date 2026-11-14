import CheapWingsKit
import SwiftUI
import UIKit

struct SearchView: View {
    @Bindable var model: SearchModel
    @Environment(\.scenePhase) private var scenePhase
    @State private var picking: Side?

    enum Side: String, Identifiable {
        case origin = "From", destination = "To"
        var id: String { rawValue }
    }

    var body: some View {
        Form {
            Section("Route") {
                if model.catalog != nil {
                    RouteHeader(model: model, disabled: model.session.isRunning) { picking = $0 }
                } else {
                    TextField("From (e.g. CGK, HLP)", text: $model.originsText)
                        .textInputAutocapitalization(.characters)
                        .autocorrectionDisabled()
                    TextField("To (e.g. DPS)", text: $model.destinationsText)
                        .textInputAutocapitalization(.characters)
                        .autocorrectionDisabled()
                    if let note = model.catalogError { Text(note).font(.caption).foregroundStyle(.secondary) }
                }
            }
            Section {
                ForEach(Sources.all, id: \.self) { id in
                    Toggle(Sources.name(id), isOn: Binding(
                        get: { model.sources.contains(id) },
                        set: { on in if on { model.sources.insert(id) } else { model.sources.remove(id) } }))
                        .disabled(model.session.isRunning)
                }
            } header: {
                Text("Sources")
            } footer: {
                Text("Skiplagged prices are in US dollars, converted with Skiplagged's own rate. Hidden-city fares are left out.")
            }
            Section("Stops") {
                Picker("Max stops", selection: $model.maxStops) {
                    Text("Any").tag(UInt32?.none)
                    Text("Nonstop").tag(UInt32?.some(0))
                    Text("1").tag(UInt32?.some(1))
                    Text("2").tag(UInt32?.some(2))
                }
                .pickerStyle(.segmented)
            }
            Section("Departure dates") {
                DatePicker("From", selection: $model.dateFrom, displayedComponents: .date)
                DatePicker("Through", selection: $model.dateThrough, in: model.dateFrom..., displayedComponents: .date)
            }
            Section("Currency") {
                Picker("Currency", selection: $model.currency) {
                    ForEach(SearchModel.currencies, id: \.self) { Text($0) }
                }
                .pickerStyle(.segmented)
            }
            Section {
                if model.session.isRunning {
                    SignButton(title: "Cancel search", enabled: true, action: model.session.cancel)
                } else {
                    SignButton(title: model.searchTitle, enabled: model.canSearch, action: model.start)
                }
                Text(model.planSummary)
                    .foregroundStyle(model.canSearch || model.session.isRunning ? AnyShapeStyle(.secondary) : AnyShapeStyle(Theme.hold))
                    .font(.footnote)
            } footer: {
                Text("Searches Google Flights from this iPad while the app is open. Prices are indicative.")
            }
        }
        .navigationTitle("CheapWings")
        .sheet(item: $picking) { side in
            if let catalog = model.catalog {
                AirportPicker(title: side.rawValue, catalog: catalog,
                              selection: side == .origin ? $model.origin : $model.destination)
            }
        }
        .onChange(of: model.session.isRunning) { _, running in
            UIApplication.shared.isIdleTimerDisabled = running
        }
        .onChange(of: scenePhase) { _, phase in
            switch phase {
            case .background: model.appBackgrounded()
            case .active: model.appForegrounded()
            default: break
            }
        }
    }

}

/// The route as large airport codes (each side opens its picker), place names underneath.
struct RouteHeader: View {
    let model: SearchModel
    let disabled: Bool
    let pick: (SearchView.Side) -> Void

    var body: some View {
        ViewThatFits(in: .horizontal) {
            HStack(alignment: .top, spacing: 14) { side(.origin); arrow; side(.destination) }
            VStack(alignment: .leading, spacing: 10) { side(.origin); side(.destination) }
        }
        .padding(.vertical, 6)
    }

    private var arrow: some View {
        Image(systemName: "arrow.right").font(.title2.weight(.semibold)).foregroundStyle(.secondary)
            .padding(.top, 8).accessibilityHidden(true)
    }

    private func side(_ side: SearchView.Side) -> some View {
        let selection = side == .origin ? model.origin : model.destination
        let codes = model.codes(selection)
        return Button { pick(side) } label: {
            VStack(alignment: .leading, spacing: 4) {
                Text(codes.isEmpty ? "Choose" : codes.joined(separator: " "))
                    .codeStyle(.largeTitle)
                    .lineLimit(2).minimumScaleFactor(0.5)
                    .foregroundStyle(codes.isEmpty ? AnyShapeStyle(.secondary) : AnyShapeStyle(.primary))
                Text(model.caption(selection)).font(.subheadline).foregroundStyle(.secondary).lineLimit(2)
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
        .buttonStyle(.plain)
        .disabled(disabled)
        .accessibilityLabel("\(side.rawValue): \(model.caption(selection))")
        .accessibilityHint("Choose airports")
    }
}

/// The main action in sign yellow with black text (owner-approved design).
struct SignButton: View {
    let title: String
    let enabled: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            Text(title)
                .font(.headline)
                .frame(maxWidth: .infinity, minHeight: 50)
                .foregroundStyle(Theme.onSign)
                .background(Theme.sign.opacity(enabled ? 1 : 0.4), in: RoundedRectangle(cornerRadius: 14))
        }
        .buttonStyle(.plain)
        .disabled(!enabled)
        .listRowInsets(EdgeInsets(top: 8, leading: 12, bottom: 8, trailing: 12))
        .listRowBackground(Color.clear)
    }
}
