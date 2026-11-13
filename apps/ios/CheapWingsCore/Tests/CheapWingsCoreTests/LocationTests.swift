import CheapWingsCore
import XCTest

/// The shared location catalog and its Python-generated fixtures, through the Swift API.
final class LocationTests: XCTestCase {
    struct SearchCase: Decodable { let text: String; let within: String?; let expect: Expect }
    struct MajorCase: Decodable { let kind, id, version: String; let expect: MajorExpect }
    enum Expect: Decodable {
        case ids([String]), error(String)
        init(from decoder: Decoder) throws {
            if let ids = try? [String](from: decoder) { self = .ids(ids); return }
            struct E: Decodable { let error: String }
            self = .error(try E(from: decoder).error)
        }
    }
    struct MajorExpect: Decodable { let codes: [String]?; let rationale: String?; let error: String? }
    struct Fixtures: Decodable { let location_search: [SearchCase]; let location_major: [MajorCase] }

    static let root: URL = {
        var url = URL(fileURLWithPath: #filePath)
        for _ in 0..<6 { url.deleteLastPathComponent() }
        return url
    }()

    static let catalog: LocationCatalog = {
        let json = try! String(contentsOf: root.appendingPathComponent("backend/src/cheapwings/locations/catalog.json"), encoding: .utf8)
        return try! LocationCatalog(json: json)
    }()

    static let fixtures: Fixtures = try! JSONDecoder().decode(
        Fixtures.self, from: Data(contentsOf: root.appendingPathComponent("contracts/fixtures/core/core_fixtures.json")))

    func testLocationSearch() {
        for c in Self.fixtures.location_search {
            switch (Result { try Self.catalog.search(text: c.text, within: c.within) }, c.expect) {
            case (.success(let found), .ids(let ids)):
                XCTAssertEqual(found.prefix(15).map(\.id), ids, "\(c.text) within \(c.within ?? "-")")
            case (.failure(CatalogError.Failed(let code, _)), .error(let want)):
                XCTAssertEqual(code, want, c.text)
            case (let got, _):
                XCTFail("\(c.text): got \(got)")
            }
        }
        XCTAssertEqual(Self.fixtures.location_search.count, 54)
    }

    func testMajorResolution() {
        for c in Self.fixtures.location_major {
            do {
                let r = try Self.catalog.resolveMajor(kind: c.kind, id: c.id, version: c.version)
                XCTAssertEqual(r.codes, c.expect.codes, c.id)
                XCTAssertEqual(r.rationale, c.expect.rationale)
            } catch CatalogError.Failed(let code, _) {
                XCTAssertEqual(code, c.expect.error, "\(c.kind) \(c.id)")
            } catch {
                XCTFail("\(c.id): \(error)")
            }
        }
    }

    func testAirportTimezoneAndChanges() {
        XCTAssertEqual(Self.catalog.airport(code: "HND")?.timezone, "Asia/Tokyo")
        let legs = [FliLeg(origin: "CGK", destination: "NRT", airline: "GA", flightNumber: "1", departLocal: "", arriveLocal: ""),
                    FliLeg(origin: "HND", destination: "ITM", airline: "NH", flightNumber: "2", departLocal: "", arriveLocal: "")]
        XCTAssertEqual(fliAirportChanges(offer: FliOffer(price: "1", currency: "IDR", legs: legs)), [AirportChange(from: "NRT", to: "HND")])
    }
}
