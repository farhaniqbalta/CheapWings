import CheapWingsCore
import Foundation

/// IATA airline code → name, from `contracts/airlines.json` (generated from the same fli table the
/// web provider uses, so both apps show the same names). Fli pages carry only codes.
public struct AirlineNames: Sendable {
    private let names: [String: String]

    public init(json: Data) throws {
        struct File: Decodable { let airlines: [String: String] }
        names = try JSONDecoder().decode(File.self, from: json).airlines
    }

    public func name(_ code: String) -> String? { names[code] }

    /// "All Nippon Airways NH 856", "Singapore Airlines SQ 951 and SQ 632",
    /// "Garuda Indonesia GA 878, Korean Air KE 2101"; unknown codes show the code only.
    public func flightsText(_ legs: [FliLeg]) -> String {
        var groups: [(airline: String, numbers: [String])] = []
        for leg in legs {
            let number = "\(leg.airline) \(leg.flightNumber)"
            if groups.last?.airline == leg.airline { groups[groups.count - 1].numbers.append(number) }
            else { groups.append((leg.airline, [number])) }
        }
        return groups.map { group in
            let numbers = group.numbers.joined(separator: " and ")
            return name(group.airline).map { "\($0) \(numbers)" } ?? numbers
        }.joined(separator: ", ")
    }
}
