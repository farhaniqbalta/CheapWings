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

    public struct Carrier: Sendable, Equatable {
        public let code: String
        public let name: String?
        public init(code: String, name: String?) {
            self.code = code
            self.name = name
        }
    }

    /// Distinct carriers in flight order (consecutive repeats collapsed).
    public func carriers(_ legs: [FliLeg]) -> [Carrier] {
        var out: [Carrier] = []
        for leg in legs where out.last?.code != leg.airline { out.append(Carrier(code: leg.airline, name: name(leg.airline))) }
        return out
    }

    /// "Garuda Indonesia and Korean Air"; an unknown carrier shows its code.
    public func carriersText(_ legs: [FliLeg]) -> String {
        carriers(legs).map { $0.name ?? $0.code }.joined(separator: " and ")
    }

    /// "SQ 951 and SQ 632" (one carrier) or "GA 878, KE 2101" (several).
    public static func numbersText(_ legs: [FliLeg]) -> String {
        let numbers = legs.map { "\($0.airline) \($0.flightNumber)" }
        return Set(legs.map(\.airline)).count <= 1 ? numbers.joined(separator: " and ") : numbers.joined(separator: ", ")
    }

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
