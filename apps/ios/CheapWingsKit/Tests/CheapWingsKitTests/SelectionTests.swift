import CheapWingsCore
@testable import CheapWingsKit
import XCTest

/// The repository's shared location catalog (same file the app bundles).
let testCatalog: LocationCatalog = {
    var url = URL(fileURLWithPath: #filePath)
    for _ in 0..<6 { url.deleteLastPathComponent() }
    let json = try! String(contentsOf: url.appendingPathComponent("backend/src/cheapwings/locations/catalog.json"), encoding: .utf8)
    return try! LocationCatalog(json: json)
}()

let tokyo = AirportToken.major(kind: "city", locationID: "metro:JP:TYO", name: "Tokyo")
let osaka = AirportToken.major(kind: "city", locationID: "metro:JP:OSA", name: "Osaka")

final class SelectionTests: XCTestCase {
    func testStackedPlacesResolveToUnionInOrder() throws {
        let side = AirportSelection([tokyo, .airport("CGK"), osaka])
        XCTAssertEqual(try side.codes(using: testCatalog), ["HND", "NRT", "CGK", "ITM", "KIX"])
        XCTAssertEqual(side.majorIDs, ["metro:JP:TYO", "metro:JP:OSA"])
    }

    func testDuplicatesAreIgnored() throws {
        var side = AirportSelection([tokyo])
        side.add(.airport("HND"), using: testCatalog)  // already covered by Tokyo
        side.add(tokyo, using: testCatalog)
        XCTAssertEqual(side.tokens, [tokyo])
        side.add(.airport("CGK"), using: testCatalog)
        side.add(.airport("CGK"), using: testCatalog)
        XCTAssertEqual(side.tokens, [tokyo, .airport("CGK")])
    }

    func testRemovingAirportFromMajorExpandsIntoPlainAirports() throws {
        var side = AirportSelection([.airport("CGK"), tokyo, osaka])
        side.remove(code: "NRT", using: testCatalog)
        XCTAssertEqual(side.tokens, [.airport("CGK"), .airport("HND"), osaka])
        side.remove(code: "CGK", using: testCatalog)
        XCTAssertEqual(side.tokens, [.airport("HND"), osaka])
        XCTAssertEqual(try side.codes(using: testCatalog), ["HND", "ITM", "KIX"])
    }

    func testRemovingWholeToken() {
        var side = AirportSelection([tokyo, .airport("CGK")])
        side.remove(token: tokyo)
        XCTAssertEqual(side.tokens, [.airport("CGK")])
    }

    func testNoMajorMappingThrows() {
        let side = AirportSelection([.major(kind: "city", locationID: "city:AE:Abu%20Dhabi:Abu%20Dhabi", name: "Abu Dhabi")])
        XCTAssertThrowsError(try side.codes(using: testCatalog)) { error in
            guard case CatalogError.Failed(let code, _) = error else { return XCTFail("\(error)") }
            XCTAssertEqual(code, "no_major_mapping")
        }
    }

    func testRestoreRebuildsTokens() throws {
        let side = AirportSelection.restore(codes: ["HND", "NRT", "CGK"], majorIDs: ["metro:JP:TYO"], catalog: testCatalog)
        XCTAssertEqual(side.tokens, [tokyo, .airport("CGK")])
        // No catalog, or a Major id it no longer knows: fall back to the stored codes.
        XCTAssertEqual(AirportSelection.restore(codes: ["HND"], majorIDs: ["metro:JP:TYO"], catalog: nil).tokens, [.airport("HND")])
        XCTAssertEqual(AirportSelection.restore(codes: ["CGK"], majorIDs: ["metro:XX:NOPE"], catalog: testCatalog).tokens, [.airport("CGK")])
    }

    func testRequestFromSelectionsKeepsMajorsAndStops() throws {
        let request = try SearchRequest.make(origin: AirportSelection([.airport("CGK")]),
                                             destination: AirportSelection([tokyo]),
                                             dateFrom: "2026-12-15", dateThrough: "2026-12-17", currency: "IDR",
                                             maxStops: 1, catalog: testCatalog)
        XCTAssertEqual(request.origins, ["CGK"])
        XCTAssertEqual(request.destinations, ["HND", "NRT"])
        XCTAssertEqual(request.destinationMajorIDs, ["metro:JP:TYO"])
        XCTAssertEqual(request.originMajorIDs, [])
        XCTAssertEqual(request.maxStops, 1)
        XCTAssertEqual(try request.plan().count, 6)
        XCTAssertEqual(SearchRequest(stored: request.stored), request)
    }

    func testMaxStopsHidesLongerItineraries() async throws {
        let twoLegs = twoLegPage("CGK", via: "SUB", "DPS", "2026-12-15")
        let oneDay = { (stops: UInt32?) in
            SearchRequest(origins: ["CGK"], destinations: ["DPS"], dateFrom: "2026-12-15",
                          dateThrough: "2026-12-15", currency: "IDR", maxStops: stops)
        }
        let nonstopOnly = oneDay(0)
        var events: [SearchEvent] = []
        for await e in SearchEngine(transport: FakeTransport([twoLegs]), maxInFlight: 1, sleep: FakeClock().sleep).run(nonstopOnly, combos: try nonstopOnly.plan()) {
            events.append(e)
        }
        XCTAssertTrue(events.allSatisfy { if case .offers = $0 { return false } else { return true } })
        // Only the stop limit removed flights: the route/date finished, it did not fail.
        XCTAssertFalse(events.contains { if case .comboFailed = $0 { return true } else { return false } })
        XCTAssertTrue(events.contains { if case .offersHidden(_, [SearchEngine.stopLimitReason]) = $0 { return true } else { return false } })

        let upToOne = oneDay(1)
        var kept = 0
        for await e in SearchEngine(transport: FakeTransport([twoLegs]), maxInFlight: 1, sleep: FakeClock().sleep).run(upToOne, combos: try upToOne.plan()) {
            if case .offers(let o) = e { kept += o.count }
        }
        XCTAssertEqual(kept, 1)
    }
}

/// One priced two-leg itinerary (origin → via → destination) on `date`.
func twoLegPage(_ origin: String, via: String, _ destination: String, _ date: String) -> FetchedPage {
    let ymd = date.split(separator: "-").map { String(Int($0)!) }.joined(separator: ",")
    func leg(_ o: String, _ d: String, _ flight: Int, depart: String, arrive: String) -> String {
        var fl = Array(repeating: "null", count: 23)
        fl[3] = "\"\(o)\""; fl[6] = "\"\(d)\""
        fl[8] = depart; fl[10] = arrive; fl[11] = "60"
        fl[20] = "[\(ymd)]"; fl[21] = "[\(ymd)]"
        fl[22] = "[\"GA\",\"\(flight)\",null]"
        return "[\(fl.joined(separator: ","))]"
    }
    let legs = [leg(origin, via, 300, depart: "[6,5]", arrive: "[7,30]"), leg(via, destination, 344, depart: "[8,30]", arrive: "[9,40]")]
    let detail = "[null,null,[\(legs.joined(separator: ","))],null,null,null,null,null,null,215]"
    let html = "<script>AF_initDataCallback({key: 'ds:1', hash: '2', data:[null,null,[[[\(detail),[[null,1500000],\"GgUaA0lEUg\"]]]],null], sideChannel: {}});</script>"
    return FetchedPage(status: 200, body: Data(html.utf8), refusedRedirect: nil)
}
