import CheapWingsCore
import Foundation

/// One chosen item on a side of the route: a single airport, or a place's curated
/// "Major airports" (resolved through the Rust catalog, never guessed).
public enum AirportToken: Sendable, Hashable {
    case airport(String)
    case major(kind: String, locationID: String, name: String)
}

/// One side of the route as an ordered list of tokens. Editing a Major place (removing one of
/// its airports) turns it into plain airport tokens, so a Major token always means the full set.
public struct AirportSelection: Sendable, Equatable {
    public private(set) var tokens: [AirportToken]

    public init(_ tokens: [AirportToken] = []) { self.tokens = tokens }

    /// Union of all tokens' airports, first occurrence order.
    public func codes(using catalog: LocationCatalog) throws -> [String] {
        var seen = Set<String>()
        return try tokens.flatMap { try Self.codes(of: $0, catalog) }.filter { seen.insert($0).inserted }
    }

    public var majorIDs: [String] {
        tokens.compactMap { if case .major(_, let id, _) = $0 { return id } else { return nil } }
    }

    /// Adds a token unless it, or (for an airport) a Major place covering it, is already there.
    public mutating func add(_ token: AirportToken, using catalog: LocationCatalog) {
        guard !tokens.contains(token) else { return }
        if case .airport(let code) = token, (try? codes(using: catalog))?.contains(code) == true { return }
        tokens.append(token)
    }

    public mutating func remove(token: AirportToken) {
        tokens.removeAll { $0 == token }
    }

    /// Removes one airport wherever it appears; a Major place containing it is expanded in place
    /// into its other airports.
    public mutating func remove(code: String, using catalog: LocationCatalog) {
        tokens = tokens.flatMap { token -> [AirportToken] in
            switch token {
            case .airport(let c): return c == code ? [] : [token]
            case .major:
                guard let codes = try? Self.codes(of: token, catalog), codes.contains(code) else { return [token] }
                return codes.filter { $0 != code }.map(AirportToken.airport)
            }
        }
        var seen = Set<AirportToken>()
        tokens = tokens.filter { seen.insert($0).inserted }
    }

    /// Rebuilds a stored side: intact Major places first, then the remaining airports. Falls back
    /// to plain codes when the catalog is missing or no longer knows a place.
    public static func restore(codes: [String], majorIDs: [String], catalog: LocationCatalog?) -> AirportSelection {
        var selection = AirportSelection()
        var covered = Set<String>()
        if let catalog {
            for id in majorIDs {
                guard let place = catalog.location(id: id) else { continue }
                let token = AirportToken.major(kind: place.kind, locationID: id, name: place.name)
                guard let placeCodes = try? Self.codes(of: token, catalog), Set(placeCodes).isSubset(of: codes) else { continue }
                selection.tokens.append(token)
                covered.formUnion(placeCodes)
            }
        }
        selection.tokens += codes.filter { !covered.contains($0) }.map(AirportToken.airport)
        return selection
    }

    private static func codes(of token: AirportToken, _ catalog: LocationCatalog) throws -> [String] {
        switch token {
        case .airport(let code): return [code]
        case .major(let kind, let id, _): return try catalog.resolveMajor(kind: kind, id: id, version: catalog.version()).codes
        }
    }
}

extension SearchRequest {
    /// Resolves both sides to airport codes; the request keeps the intact Major ids for restore.
    public static func make(origin: AirportSelection, destination: AirportSelection, dateFrom: String,
                            dateThrough: String, currency: String, maxStops: UInt32?,
                            catalog: LocationCatalog) throws -> SearchRequest {
        SearchRequest(origins: try origin.codes(using: catalog), destinations: try destination.codes(using: catalog),
                      dateFrom: dateFrom, dateThrough: dateThrough, currency: currency, maxStops: maxStops,
                      originMajorIDs: origin.majorIDs, destinationMajorIDs: destination.majorIDs)
    }
}
