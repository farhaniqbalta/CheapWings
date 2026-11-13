import CheapWingsCore
import Foundation

/// What the user picked for one side of the route: exact airports, or the curated
/// Major airports of a city/country (resolved through the Rust catalog, never guessed).
public enum AirportSelection: Sendable, Equatable {
    case specific([String])
    case major(kind: String, locationID: String, name: String)

    public func codes(using catalog: LocationCatalog) throws -> [String] {
        switch self {
        case .specific(let codes):
            return codes
        case .major(let kind, let id, _):
            return try catalog.resolveMajor(kind: kind, id: id, version: catalog.version()).codes
        }
    }

    public var majorID: String? {
        if case .major(_, let id, _) = self { return id }
        return nil
    }

    /// Rebuilds a stored side of a request (codes, plus the Major location id if one was used).
    public static func restore(codes: [String], majorID: String?, catalog: LocationCatalog?) -> AirportSelection {
        guard let majorID, let place = catalog?.location(id: majorID) else { return .specific(codes) }
        return .major(kind: place.kind, locationID: majorID, name: place.name)
    }
}

extension SearchRequest {
    /// Resolves the selections to airport codes; the request keeps the Major ids for display.
    public static func make(origin: AirportSelection, destination: AirportSelection, dateFrom: String,
                            dateThrough: String, currency: String, maxStops: UInt32?,
                            catalog: LocationCatalog) throws -> SearchRequest {
        SearchRequest(origins: try origin.codes(using: catalog), destinations: try destination.codes(using: catalog),
                      dateFrom: dateFrom, dateThrough: dateThrough, currency: currency, maxStops: maxStops,
                      originMajorID: origin.majorID, destinationMajorID: destination.majorID)
    }
}
