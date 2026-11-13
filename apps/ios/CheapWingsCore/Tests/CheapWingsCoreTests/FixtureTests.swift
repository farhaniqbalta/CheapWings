import CheapWingsCore
import XCTest

/// Shared fixtures (generated from the Python reference) through the UniFFI Swift API.
final class FixtureTests: XCTestCase {
    struct MoneyCase: Decodable { let op: String; let amount, rate, minor: String?; let currency: String; let expect: String? }
    struct InstantJ: Decodable { let y: Int32; let mo, d, h, mi, s, us: UInt32; let offset: Int32 }
    struct SegmentJ: Decodable {
        let ordinal: UInt32
        let marketing, operating, flight, origin, destination: String
        let depart, arrive: InstantJ
    }
    struct FingerprintCase: Decodable { let segments: [SegmentJ]; let expect: String }
    struct OfferJ: Decodable { let id, price_status, hidden_city, comparison_status: String; let amount: String? }
    struct RankingCase: Decodable { let groups: [[OfferJ]]; let best, lowest: [String] }
    struct TfsCase: Decodable { let origin, destination, date, expect: String }
    struct LegJ: Decodable { let origin, destination, airline, flight_number, depart_local, arrive_local: String }
    struct OfferExpectJ: Decodable { let price: String; let currency: String?; let legs: [LegJ] }
    struct PageExpect: Decodable { let offers: [OfferExpectJ]?; let unpriced: UInt32?; let error: String? }
    struct PageCase: Decodable { let html: String; let expect: PageExpect }
    struct Fixtures: Decodable {
        let money: [MoneyCase]
        let fingerprint: [FingerprintCase]
        let ranking: [RankingCase]
        let fli_tfs: [TfsCase]
        let fli_pages: [PageCase]
    }

    static let fixtures: Fixtures = {
        var url = URL(fileURLWithPath: #filePath)
        for _ in 0..<6 { url.deleteLastPathComponent() }  // → repository root
        let file = url.appendingPathComponent("contracts/fixtures/core/core_fixtures.json")
        return try! JSONDecoder().decode(Fixtures.self, from: Data(contentsOf: file))
    }()

    func testMoney() {
        let cases = Self.fixtures.money
        for c in cases {
            let got: String?
            switch c.op {
            case "fx": got = try? fxConvert(amount: c.amount!, rate: c.rate!, quoteCurrency: c.currency)
            case "from_minor": got = try? fromMinorUnits(minor: c.minor!, currency: c.currency)
            default: got = try? asMinorUnits(amount: c.amount!, currency: c.currency)
            }
            XCTAssertEqual(got, c.expect, "\(c.op) \(c.amount ?? c.minor ?? "") \(c.currency)")
        }
        XCTAssertEqual(cases.count, 3006)
    }

    func testFingerprint() {
        let instant = { (i: InstantJ) in LocalInstant(y: i.y, mo: i.mo, d: i.d, h: i.h, mi: i.mi, s: i.s, us: i.us, offset: i.offset) }
        for c in Self.fixtures.fingerprint {
            let segments = c.segments.map {
                Segment(ordinal: $0.ordinal, marketing: $0.marketing, operating: $0.operating, flight: $0.flight,
                        origin: $0.origin, destination: $0.destination, depart: instant($0.depart), arrive: instant($0.arrive))
            }
            XCTAssertEqual(fingerprint(segments: segments), c.expect)
        }
        XCTAssertEqual(Self.fixtures.fingerprint.count, 500)
    }

    func testRanking() {
        for c in Self.fixtures.ranking {
            let groups = c.groups.map { $0.map {
                RankOffer(id: $0.id, priceStatus: $0.price_status, hiddenCity: $0.hidden_city,
                          comparisonStatus: $0.comparison_status, amount: $0.amount)
            } }
            XCTAssertEqual(bestCheckedDeal(groups: groups), c.best)
            XCTAssertEqual(lowestAdvertised(groups: groups), c.lowest)
        }
        XCTAssertEqual(Self.fixtures.ranking.count, 300)
    }

    func testFliTfs() {
        for c in Self.fixtures.fli_tfs {
            let url = fliSearchUrl(origin: c.origin, destination: c.destination, date: c.date, currency: "IDR", country: "ID")
            XCTAssertEqual(url, "https://www.google.com/travel/flights?tfs=\(c.expect)&hl=en&gl=ID&curr=IDR")
        }
        XCTAssertEqual(Self.fixtures.fli_tfs.count, 50)
    }

    func testFliPages() {
        for (i, c) in Self.fixtures.fli_pages.enumerated() {
            do {
                let page = try fliDecodePage(html: c.html)
                XCTAssertNil(c.expect.error, "page #\(i) should fail")
                XCTAssertEqual(page.unpriced, c.expect.unpriced, "page #\(i) unpriced")
                let expected = (c.expect.offers ?? []).map { o in
                    FliOffer(price: o.price, currency: o.currency, legs: o.legs.map {
                        FliLeg(origin: $0.origin, destination: $0.destination, airline: $0.airline,
                               flightNumber: $0.flight_number, departLocal: $0.depart_local, arriveLocal: $0.arrive_local)
                    })
                }
                XCTAssertEqual(page.offers, expected, "page #\(i) offers")
            } catch FliDecodeError.Failed(let code, _) {
                XCTAssertEqual(code, c.expect.error, "page #\(i) error")
            } catch {
                XCTFail("page #\(i): unexpected \(error)")
            }
        }
        XCTAssertEqual(Self.fixtures.fli_pages.count, 45)
    }

    func testFliErrorDoesNotCrash() {
        XCTAssertThrowsError(try fliDecodePage(html: "<html></html>")) { error in
            guard case FliDecodeError.Failed(let code, _) = error else { return XCTFail("\(error)") }
            XCTAssertEqual(code, "schema_changed")
        }
    }
}
