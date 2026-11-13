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

final class SelectionTests: XCTestCase {
    func testMajorSelectionResolvesCuratedCodes() throws {
        let japan = AirportSelection.major(kind: "country", locationID: "country:JP", name: "Japan")
        XCTAssertEqual(try japan.codes(using: testCatalog), ["CTS", "FUK", "HND", "ITM", "KIX", "NGO", "NRT", "OKA"])
        XCTAssertEqual(japan.majorID, "country:JP")
        XCTAssertEqual(AirportSelection.specific(["CGK", "HLP"]).majorID, nil)
    }

    func testNoMajorMappingThrows() {
        let noMapping = AirportSelection.major(kind: "city", locationID: "city:AE:Abu%20Dhabi:Abu%20Dhabi", name: "Abu Dhabi")
        XCTAssertThrowsError(try noMapping.codes(using: testCatalog)) { error in
            guard case CatalogError.Failed(let code, _) = error else { return XCTFail("\(error)") }
            XCTAssertEqual(code, "no_major_mapping")
        }
    }

    func testRequestFromSelectionsKeepsMajorAndStops() throws {
        let request = try SearchRequest.make(origin: .specific(["CGK"]),
                                             destination: .major(kind: "city", locationID: "metro:JP:TYO", name: "Tokyo"),
                                             dateFrom: "2026-12-15", dateThrough: "2026-12-17", currency: "IDR",
                                             maxStops: 1, catalog: testCatalog)
        XCTAssertEqual(request.origins, ["CGK"])
        XCTAssertEqual(request.destinations, ["HND", "NRT"])
        XCTAssertEqual(request.destinationMajorID, "metro:JP:TYO")
        XCTAssertNil(request.originMajorID)
        XCTAssertEqual(request.maxStops, 1)
        XCTAssertEqual(try request.plan().count, 6)
        // Round trip through the stored form keeps the new fields.
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
        for await e in SearchEngine(transport: FakeTransport([twoLegs]), sleep: FakeClock().sleep).run(nonstopOnly, combos: try nonstopOnly.plan()) {
            events.append(e)
        }
        XCTAssertTrue(events.allSatisfy { if case .offers = $0 { return false } else { return true } })
        XCTAssertTrue(events.contains { if case .comboFailed(_, "cross_check: stops 1 > 0") = $0 { return true } else { return false } })

        let upToOne = oneDay(1)
        var kept = 0
        for await e in SearchEngine(transport: FakeTransport([twoLegs]), sleep: FakeClock().sleep).run(upToOne, combos: try upToOne.plan()) {
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
