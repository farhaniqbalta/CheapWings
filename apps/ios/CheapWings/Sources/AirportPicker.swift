import CheapWingsCore
import CheapWingsKit
import SwiftUI

/// Pick airports by typing an airport, city or country (P4.10 semantics): airports toggle into a
/// Specific selection; a city/country opens its airports and offers its curated Major list when
/// one exists. Browsing a place never selects it.
struct AirportPicker: View {
    let title: String
    let catalog: LocationCatalog
    @Binding var selection: AirportSelection
    @Environment(\.dismiss) private var dismiss
    @State private var query = ""

    private static let shownLimit = 50

    var body: some View {
        NavigationStack {
            List {
                if case .specific(let codes) = selection, !codes.isEmpty {
                    Section("Selected airports") {
                        ForEach(codes, id: \.self) { code in
                            Button { toggle(code) } label: {
                                Label("\(code) · \(catalog.airport(code: code)?.name ?? "")", systemImage: "checkmark.circle.fill")
                            }
                        }
                    }
                } else if case .major(_, _, let name) = selection {
                    Section("Selected") { Label("\(name) · Major airports", systemImage: "checkmark.circle.fill") }
                }
                results
            }
            .searchable(text: $query, placement: .navigationBarDrawer(displayMode: .always),
                        prompt: "Airport, city or country")
            .autocorrectionDisabled()
            .navigationTitle(title)
            .navigationBarTitleDisplayMode(.inline)
            .toolbar { ToolbarItem(placement: .confirmationAction) { Button("Done") { dismiss() } } }
            .navigationDestination(for: PlaceLink.self) { link in
                PlaceAirports(catalog: catalog, place: link.location, selection: $selection, onMajor: { dismiss() })
            }
        }
    }

    @ViewBuilder private var results: some View {
        let found = (try? catalog.search(text: query, within: nil)) ?? []
        let shown = Array(found.prefix(Self.shownLimit))
        ForEach(["airport", "city", "country"], id: \.self) { kind in
            let group = shown.filter { $0.kind == kind }
            if !group.isEmpty {
                Section(kind == "airport" ? "Airports" : kind == "city" ? "Cities" : "Countries") {
                    ForEach(group, id: \.id) { location in
                        if kind == "airport", let code = location.code {
                            Button { toggle(code) } label: { AirportRow(location: location, selected: isSelected(code)) }
                        } else {
                            NavigationLink(value: PlaceLink(location: location)) {
                                VStack(alignment: .leading) {
                                    Text(location.name)
                                    Text("\(location.countryName) · \(location.codes.count) airports")
                                        .font(.caption).foregroundStyle(.secondary)
                                }
                            }
                        }
                    }
                }
            }
        }
        if found.count > Self.shownLimit {
            Text("\(found.count - Self.shownLimit) more — refine your search").font(.caption).foregroundStyle(.secondary)
        } else if !query.isEmpty && found.isEmpty {
            Text("No matching airports, cities or countries").foregroundStyle(.secondary)
        }
    }

    private func isSelected(_ code: String) -> Bool {
        if case .specific(let codes) = selection { return codes.contains(code) }
        return false
    }

    private func toggle(_ code: String) {
        var codes: [String] = []
        if case .specific(let current) = selection { codes = current }
        if let i = codes.firstIndex(of: code) { codes.remove(at: i) } else { codes.append(code) }
        selection = .specific(codes)
    }
}

/// Navigation value for browsing a city/country.
struct PlaceLink: Hashable {
    let location: Location
    static func == (a: PlaceLink, b: PlaceLink) -> Bool { a.location.id == b.location.id }
    func hash(into hasher: inout Hasher) { hasher.combine(location.id) }
}

struct AirportRow: View {
    let location: Location
    let selected: Bool

    var body: some View {
        HStack {
            VStack(alignment: .leading) {
                Text("\(location.code ?? "") · \(location.name)")
                Text([location.city, location.countryName].compactMap { $0 }.joined(separator: ", "))
                    .font(.caption).foregroundStyle(.secondary)
            }
            Spacer()
            if selected { Image(systemName: "checkmark").foregroundStyle(.tint) }
        }
    }
}

/// A city/country's airports, with "Use Major airports" only when a curated list exists.
struct PlaceAirports: View {
    let catalog: LocationCatalog
    let place: Location
    @Binding var selection: AirportSelection
    let onMajor: () -> Void

    var body: some View {
        let airports = (try? catalog.airportsOf(id: place.id)) ?? []
        let major = catalog.hasMajor(id: place.id)
            ? try? catalog.resolveMajor(kind: place.kind, id: place.id, version: catalog.version()) : nil
        List {
            if let major {
                Section {
                    Button {
                        selection = .major(kind: place.kind, locationID: place.id, name: place.name)
                        onMajor()
                    } label: {
                        Label("Use Major airports (\(major.codes.count)): \(major.codes.joined(separator: ", "))",
                              systemImage: "star.circle")
                    }
                } footer: {
                    Text(major.rationale)
                }
            } else {
                Section { Text("No curated Major list for \(place.name) — pick specific airports.").foregroundStyle(.secondary) }
            }
            Section("Airports in \(place.name)") {
                ForEach(airports, id: \.id) { airport in
                    if let code = airport.code {
                        Button { toggle(code) } label: { AirportRow(location: airport, selected: isSelected(code)) }
                    }
                }
            }
        }
        .navigationTitle(place.name)
    }

    private func isSelected(_ code: String) -> Bool {
        if case .specific(let codes) = selection { return codes.contains(code) }
        return false
    }

    private func toggle(_ code: String) {
        var codes: [String] = []
        if case .specific(let current) = selection { codes = current }
        if let i = codes.firstIndex(of: code) { codes.remove(at: i) } else { codes.append(code) }
        selection = .specific(codes)
    }
}
