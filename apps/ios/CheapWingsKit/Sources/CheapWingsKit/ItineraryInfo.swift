import CheapWingsCore
import Foundation

public struct Layover: Sendable, Equatable {
    public let airport: String
    /// Set when the next flight leaves from a different airport (e.g. NRT → HND).
    public let toAirport: String?
    public let minutes: Int?
}

/// Display facts for one itinerary. Google sends naive local times; durations use each airport's
/// IANA time zone from the catalog and the OS time-zone database, and are omitted (never guessed)
/// when a zone is unknown.
public struct ItineraryInfo: Sendable, Equatable {
    public let stops: Int
    public let totalMinutes: Int?
    public let legMinutes: [Int?]
    public let layovers: [Layover]
    public let airportChanges: [AirportChange]

    public static func make(offer: FliOffer, catalog: LocationCatalog) -> ItineraryInfo {
        func instant(_ local: String, at airport: String) -> Date? {
            guard let zone = catalog.airport(code: airport)?.timezone.flatMap(TimeZone.init(identifier:)) else { return nil }
            let parts = local.split(whereSeparator: { "-T:".contains($0) }).compactMap { Int($0) }
            guard parts.count == 5 else { return nil }
            var calendar = Calendar(identifier: .gregorian)
            calendar.timeZone = zone
            return calendar.date(from: DateComponents(year: parts[0], month: parts[1], day: parts[2], hour: parts[3], minute: parts[4]))
        }
        func minutes(_ from: Date?, _ to: Date?) -> Int? {
            guard let from, let to else { return nil }
            let minutes = Int(to.timeIntervalSince(from) / 60)
            return minutes >= 0 ? minutes : nil  // inconsistent times: unknown, never negative
        }
        let legs = offer.legs
        let departs = legs.map { instant($0.departLocal, at: $0.origin) }
        let arrives = legs.map { instant($0.arriveLocal, at: $0.destination) }
        let layovers = legs.indices.dropLast().map { i in
            Layover(airport: legs[i].destination,
                    toAirport: legs[i].destination == legs[i + 1].origin ? nil : legs[i + 1].origin,
                    minutes: minutes(arrives[i], departs[i + 1]))
        }
        return ItineraryInfo(
            stops: max(legs.count - 1, 0),
            totalMinutes: minutes(departs.first ?? nil, arrives.last ?? nil),
            legMinutes: legs.indices.map { minutes(departs[$0], arrives[$0]) },
            layovers: layovers,
            airportChanges: fliAirportChanges(offer: offer))
    }

    /// `435` → `"7h 15m"`.
    public static func durationText(_ minutes: Int) -> String {
        let (h, m) = (minutes / 60, minutes % 60)
        if h == 0 { return "\(m)m" }
        return m == 0 ? "\(h)h" : "\(h)h \(m)m"
    }
}
