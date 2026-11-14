import CheapWingsCore
import CheapWingsKit
import SwiftUI

/// Pick airports for one side of the route. A city or country adds its curated Major airports
/// in one tap; single airports stack beside them. Removing one airport of a Major place turns
/// that place into its remaining airports (owner decision, P5.5).
struct AirportPicker: View {
    let title: String
    let catalog: LocationCatalog
    @Binding var selection: AirportSelection
    @Environment(\.dismiss) private var dismiss
    @State private var query = ""

    private static let shownLimit = 50

    var body: some View {
        let chosen = Set((try? selection.codes(using: catalog)) ?? [])
        NavigationStack {
            List {
                if !selection.tokens.isEmpty {
                    Section("Selected") {
                        ForEach(selection.tokens, id: \.self) { token in
                            SelectedTokenRow(token: token, catalog: catalog, selection: $selection)
                        }
                        .onDelete { offsets in
                            for token in offsets.map({ selection.tokens[$0] }) { selection.remove(token: token) }
                        }
                    }
                }
                results(chosen: chosen)
            }
            .searchable(text: $query, placement: .navigationBarDrawer(displayMode: .always),
                        prompt: "City, country or airport")
            .autocorrectionDisabled()
            .navigationTitle(title)
            .navigationBarTitleDisplayMode(.inline)
            .toolbar { ToolbarItem(placement: .confirmationAction) { Button("Done") { dismiss() } } }
            .navigationDestination(for: PlaceLink.self) { link in
                PlaceAirports(catalog: catalog, place: link.location, selection: $selection)
            }
        }
    }

    @ViewBuilder private func results(chosen: Set<String>) -> some View {
        let result = Result { try catalog.searchPage(text: query, within: nil, limit: UInt32(Self.shownLimit)) }
        let shown = (try? result.get())?.locations ?? []
        let total = Int((try? result.get())?.total ?? 0)
        // Places first: Major airports of a city or country is the common choice.
        ForEach(["city", "country", "airport"], id: \.self) { kind in
            let group = shown.filter { $0.kind == kind }
            if !group.isEmpty {
                Section(kind == "airport" ? "Airports" : kind == "city" ? "Cities" : "Countries") {
                    ForEach(group, id: \.id) { location in
                        if kind == "airport", let code = location.code {
                            AirportToggleRow(location: location, selected: chosen.contains(code)) {
                                toggle(code, chosen: chosen)
                            }
                        } else {
                            PlaceRow(place: location, catalog: catalog, selection: $selection)
                        }
                    }
                }
            }
        }
        if case .failure(CatalogError.Failed("too_long", _)) = result {
            Text("Search text is too long. Use up to 100 characters.").foregroundStyle(.secondary)
        } else if total > shown.count {
            Text("\(total - shown.count) more matches. Type more to narrow the list.")
                .font(.caption).foregroundStyle(.secondary)
        } else if !query.isEmpty && shown.isEmpty {
            Text("No city, country or airport matches “\(query)”.").foregroundStyle(.secondary)
        }
    }

    private func toggle(_ code: String, chosen: Set<String>) {
        if chosen.contains(code) { selection.remove(code: code, using: catalog) }
        else { selection.add(.airport(code), using: catalog) }
    }
}

/// A chosen token. A Major place lists its airports as removable chips.
struct SelectedTokenRow: View {
    let token: AirportToken
    let catalog: LocationCatalog
    @Binding var selection: AirportSelection

    var body: some View {
        switch token {
        case .airport(let code):
            HStack {
                Text(code).codeStyle()
                Text(catalog.airport(code: code)?.name ?? "").foregroundStyle(.secondary)
                Spacer()
                removeButton("Remove \(code)") { selection.remove(token: token) }
            }
        case .major(_, _, let name):
            let codes = majorCodes
            VStack(alignment: .leading, spacing: 8) {
                HStack {
                    Text(name).font(.body.weight(.semibold))
                    Text("Major airports").foregroundStyle(.secondary)
                    Spacer()
                    removeButton("Remove \(name)") { selection.remove(token: token) }
                }
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(spacing: 6) {
                        ForEach(codes, id: \.self) { code in
                            Button { selection.remove(code: code, using: catalog) } label: {
                                Label(code, systemImage: "xmark").labelStyle(ChipLabelStyle())
                                    .padding(.horizontal, 14)
                                    .frame(minHeight: 44)
                                    .background(.quaternary, in: Capsule())
                            }
                            .buttonStyle(.plain)
                            .accessibilityLabel("Remove \(code) from \(name)")
                        }
                    }
                }
            }
            .padding(.vertical, 2)
        }
    }

    private var majorCodes: [String] {
        guard case .major(let kind, let id, _) = token else { return [] }
        return (try? catalog.resolveMajor(kind: kind, id: id, version: catalog.version()).codes) ?? []
    }

    private func removeButton(_ label: String, action: @escaping () -> Void) -> some View {
        Button(action: action) { Image(systemName: "xmark.circle.fill").foregroundStyle(.secondary) }
            .buttonStyle(.borderless)
            .accessibilityLabel(label)
    }
}

/// "NRT ✕" — code first, then the remove mark.
struct ChipLabelStyle: LabelStyle {
    func makeBody(configuration: Configuration) -> some View {
        HStack(spacing: 4) {
            configuration.title.codeStyle(.subheadline)
            configuration.icon.font(.caption2.weight(.bold)).foregroundStyle(.secondary)
        }
    }
}

/// A city or country: one-tap "Add major airports" when a curated list exists, and a link to
/// browse all of its airports.
struct PlaceRow: View {
    let place: Location
    let catalog: LocationCatalog
    @Binding var selection: AirportSelection

    var body: some View {
        let token = AirportToken.major(kind: place.kind, locationID: place.id, name: place.name)
        let major = catalog.hasMajor(id: place.id)
            ? try? catalog.resolveMajor(kind: place.kind, id: place.id, version: catalog.version()) : nil
        NavigationLink(value: PlaceLink(location: place)) {
            HStack {
                VStack(alignment: .leading) {
                    Text(place.name)
                    Text(major.map { "Major: \($0.codes.joined(separator: ", "))" }
                         ?? "\(place.countryName), \(place.codes.count) airports")
                        .font(.caption).foregroundStyle(.secondary)
                }
                Spacer()
                if let major {
                    if selection.tokens.contains(token) {
                        Label("Added", systemImage: "checkmark").font(.subheadline).foregroundStyle(.secondary)
                    } else {
                        Button { selection.add(token, using: catalog) } label: {
                            Text("Add \(major.codes.count) major")
                                .font(.subheadline.weight(.bold))
                                .padding(.horizontal, 14).frame(minHeight: 36)
                                .foregroundStyle(Theme.onSign)
                                .background(Theme.sign, in: Capsule())
                        }
                        .buttonStyle(.borderless)
                        .accessibilityHidden(true)  // offered as the row's own action below
                    }
                }
            }
        }
        // VoiceOver: the row opens the place; "Add major airports" is a separate action (P5.5 review).
        .accessibilityAction(named: Text("Add \(major?.codes.count ?? 0) major airports")) {
            if major != nil { selection.add(token, using: catalog) }
        }
    }
}

/// Navigation value for browsing a city/country.
struct PlaceLink: Hashable {
    let location: Location
    static func == (a: PlaceLink, b: PlaceLink) -> Bool { a.location.id == b.location.id }
    func hash(into hasher: inout Hasher) { hasher.combine(location.id) }
}

struct AirportToggleRow: View {
    let location: Location
    let selected: Bool
    let toggle: () -> Void

    var body: some View {
        Button(action: toggle) {
            HStack {
                VStack(alignment: .leading) {
                    HStack(alignment: .firstTextBaseline, spacing: 10) {
                    Text(location.code ?? "").codeStyle()
                    Text(location.name)
                }
                .foregroundStyle(.primary)
                    Text([location.city, location.countryName].compactMap { $0 }.joined(separator: ", "))
                        .font(.caption).foregroundStyle(.secondary)
                }
                Spacer()
                if selected { SelectedMark() } else {
                    Image(systemName: "plus.circle").font(.title3).foregroundStyle(.secondary)
                }
            }
        }
        .accessibilityAddTraits(selected ? .isSelected : [])
    }
}

/// All airports of a city/country, with the Major shortcut on top when one exists.
struct PlaceAirports: View {
    let catalog: LocationCatalog
    let place: Location
    @Binding var selection: AirportSelection

    var body: some View {
        let airports = (try? catalog.airportsOf(id: place.id)) ?? []
        let chosen = Set((try? selection.codes(using: catalog)) ?? [])
        let token = AirportToken.major(kind: place.kind, locationID: place.id, name: place.name)
        let major = catalog.hasMajor(id: place.id)
            ? try? catalog.resolveMajor(kind: place.kind, id: place.id, version: catalog.version()) : nil
        List {
            if let major {
                Section {
                    Button { selection.add(token, using: catalog) } label: {
                        Label("Add major airports: \(major.codes.joined(separator: ", "))", systemImage: "star.circle")
                    }
                    .disabled(selection.tokens.contains(token))
                } footer: {
                    Text(major.rationale)
                }
            } else {
                Section { Text("\(place.name) has no curated major airports. Pick the ones you want below.").foregroundStyle(.secondary) }
            }
            Section("All airports in \(place.name)") {
                ForEach(airports, id: \.id) { airport in
                    if let code = airport.code {
                        AirportToggleRow(location: airport, selected: chosen.contains(code)) {
                            if chosen.contains(code) { selection.remove(code: code, using: catalog) }
                            else { selection.add(.airport(code), using: catalog) }
                        }
                    }
                }
            }
        }
        .navigationTitle(place.name)
    }
}

/// Selected airport: black check on sign yellow (reads the same in light and dark mode).
struct SelectedMark: View {
    var body: some View {
        Image(systemName: "checkmark.circle.fill")
            .symbolRenderingMode(.palette)
            .foregroundStyle(Theme.onSign, Theme.sign)
            .font(.title3)
            .accessibilityLabel("Selected")
    }
}
