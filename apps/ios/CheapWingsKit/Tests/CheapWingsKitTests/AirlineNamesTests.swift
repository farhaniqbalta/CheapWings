import CheapWingsCore
@testable import CheapWingsKit
import XCTest

/// The repository's airline table (same file the app bundles, generated from fli).
let testAirlines: AirlineNames = {
    var url = URL(fileURLWithPath: #filePath)
    for _ in 0..<6 { url.deleteLastPathComponent() }
    return try! AirlineNames(json: Data(contentsOf: url.appendingPathComponent("contracts/airlines.json")))
}()

final class AirlineNamesTests: XCTestCase {
    func leg(_ airline: String, _ number: String) -> FliLeg {
        FliLeg(origin: "CGK", destination: "HND", airline: airline, flightNumber: number, departLocal: "", arriveLocal: "")
    }

    func testLooksUpNames() {
        XCTAssertEqual(testAirlines.name("NH"), "All Nippon Airways")
        XCTAssertEqual(testAirlines.name("GA"), "Garuda Indonesia")
        XCTAssertNil(testAirlines.name("Q9X"))
    }

    func testFlightsTextGroupsConsecutiveCarrier() {
        XCTAssertEqual(testAirlines.flightsText([leg("NH", "856")]), "All Nippon Airways NH 856")
        XCTAssertEqual(testAirlines.flightsText([leg("SQ", "951"), leg("SQ", "632")]), "Singapore Airlines SQ 951 and SQ 632")
        XCTAssertEqual(testAirlines.flightsText([leg("GA", "878"), leg("KE", "2101")]), "Garuda Indonesia GA 878, Korean Air KE 2101")
        // Unknown code: the code alone, never a guessed name.
        XCTAssertEqual(testAirlines.flightsText([leg("Q9X", "1")]), "Q9X 1")
    }

    func testCarriersAndNumbers() {
        let mixed = [leg("GA", "878"), leg("KE", "2101")]
        XCTAssertEqual(testAirlines.carriers(mixed).map(\.code), ["GA", "KE"])
        XCTAssertEqual(testAirlines.carriers(mixed).map(\.name), ["Garuda Indonesia", "Korean Air"])
        XCTAssertEqual(testAirlines.carriersText(mixed), "Garuda Indonesia and Korean Air")
        XCTAssertEqual(AirlineNames.numbersText(mixed), "GA 878, KE 2101")
        let same = [leg("SQ", "951"), leg("SQ", "632")]
        XCTAssertEqual(testAirlines.carriers(same).map(\.code), ["SQ"])
        XCTAssertEqual(testAirlines.carriersText(same), "Singapore Airlines")
        XCTAssertEqual(AirlineNames.numbersText(same), "SQ 951 and SQ 632")
        XCTAssertEqual(testAirlines.carriersText([leg("Q9X", "1")]), "Q9X")
    }

    func testBadFileThrows() {
        XCTAssertThrowsError(try AirlineNames(json: Data("{}".utf8)))
    }
}
