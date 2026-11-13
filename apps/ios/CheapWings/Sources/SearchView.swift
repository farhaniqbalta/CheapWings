import SwiftUI
import UIKit

struct SearchView: View {
    @Bindable var model: SearchModel
    @Environment(\.scenePhase) private var scenePhase

    var body: some View {
        Form {
            Section("Route") {
                TextField("From (e.g. CGK, HLP)", text: $model.originsText)
                    .textInputAutocapitalization(.characters)
                    .autocorrectionDisabled()
                TextField("To (e.g. DPS)", text: $model.destinationsText)
                    .textInputAutocapitalization(.characters)
                    .autocorrectionDisabled()
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
                    .foregroundStyle(model.canSearch || model.isRunning ? Color.secondary : Color.red)
                    .font(.footnote)
                if model.isRunning {
                    Button("Cancel", role: .destructive, action: model.cancel)
                } else {
                    Button("Search Google Flights", action: model.start)
                        .disabled(!model.canSearch)
                }
            } footer: {
                Text("Runs on this iPad only while the app is open. Prices are indicative.")
            }
        }
        .navigationTitle("CheapWings")
        .onChange(of: model.isRunning) { _, running in
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
