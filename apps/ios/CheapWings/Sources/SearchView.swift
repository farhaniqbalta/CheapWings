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
                    routeButton(.origin, model.origin)
                    routeButton(.destination, model.destination)
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
                Text(model.planSummary)
                    .foregroundStyle(model.canSearch || model.session.isRunning ? Color.secondary : Color.red)
                    .font(.footnote)
                if model.session.isRunning {
                    Button("Cancel", role: .destructive, action: model.session.cancel)
                } else {
                    Button("Search Google Flights", action: model.start)
                        .disabled(!model.canSearch)
                }
            } footer: {
                Text("Runs on this iPad only while the app is open. Prices are indicative.")
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

    private func routeButton(_ side: Side, _ selection: AirportSelection) -> some View {
        Button { picking = side } label: {
            LabeledContent(side.rawValue) {
                Text(model.label(selection)).foregroundStyle(.primary).multilineTextAlignment(.trailing)
            }
        }
        .disabled(model.session.isRunning)
    }
}
