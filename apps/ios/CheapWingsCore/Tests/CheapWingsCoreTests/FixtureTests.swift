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
    struct RouteDateJ: Decodable { let origin, destination, date: String }
    enum PlanExpectJ: Decodable {
        case combos([RouteDateJ]), error(String)
        init(from decoder: Decoder) throws {
            if let combos = try? [RouteDateJ](from: decoder) { self = .combos(combos); return }
            struct E: Decodable { let error: String }
            self = .error(try E(from: decoder).error)
        }
    }
    struct PlanCase: Decodable {
        let origins, destinations: [String]
        let from, through: String
        let max: UInt32
        let expect: PlanExpectJ
    }
    struct Fixtures: Decodable {
        let money: [MoneyCase]
        let fingerprint: [FingerprintCase]
        let ranking: [RankingCase]
        let fli_tfs: [TfsCase]
        let fli_pages: [PageCase]
        let planning: [PlanCase]
        let skiplagged: [SkipCase]
    }
    struct SkipOfferJ: Decodable {
        let id, depart_local, arrive_local, price_original: String
        let price_comparable, link: String?
        let stops: UInt32
        let carriers: [String]
    }
    struct SkipExpect: Decodable { let offers: [SkipOfferJ]?; let complete: Bool?; let error: String? }
    struct SkipCase: Decodable {
        let name, json, origin, destination, date, currency: String
        let expect: SkipExpect
    }

    static let fixtures: Fixtures = {
        var url = URL(fileURLWithPath: #filePath)
        for _ in 0..<6 { url.deleteLastPathComponent() }  // → repository root
        let file = url.appendingPathComponent("contracts/fixtures/core/core_fixtures.json")
        return try! JSONDecoder().decode(Fixtures.self, from: Data(contentsOf: file))
    }()

    func testSkiplaggedParse() {
        XCTAssertEqual(Self.fixtures.skiplagged.count, 19)
        for c in Self.fixtures.skiplagged {
            do {
                let page = try skiplaggedParse(json: c.json, origin: c.origin, destination: c.destination,
                                               date: c.date, displayCurrency: c.currency)
                let want = try XCTUnwrap(c.expect.offers, c.name)
                XCTAssertEqual(page.complete, c.expect.complete, c.name)
                XCTAssertEqual(page.offers.map(\.id), want.map(\.id), c.name)
                XCTAssertEqual(page.offers.map(\.priceOriginal), want.map(\.price_original), c.name)
                XCTAssertEqual(page.offers.map(\.priceComparable), want.map(\.price_comparable), c.name)
                XCTAssertEqual(page.offers.map(\.departLocal), want.map(\.depart_local), c.name)
                XCTAssertEqual(page.offers.map(\.stops), want.map(\.stops), c.name)
                XCTAssertEqual(page.offers.map(\.carriers), want.map(\.carriers), c.name)
                XCTAssertEqual(page.offers.map(\.link), want.map(\.link), c.name)
            } catch SkiplaggedError.Failed(let code, _) {
                XCTAssertEqual(code, c.expect.error, c.name)
            } catch {
                XCTFail("\(c.name): \(error)")
            }
        }
    }

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

    func testPlanning() {
        for (i, c) in Self.fixtures.planning.enumerated() {
            do {
                let combos = try planSearch(origins: c.origins, destinations: c.destinations,
                                            dateFrom: c.from, dateThrough: c.through, maxCombinations: c.max)
                guard case .combos(let want) = c.expect else { return XCTFail("case #\(i) should fail") }
                XCTAssertEqual(combos.map { [$0.origin, $0.destination, $0.date] },
                               want.map { [$0.origin, $0.destination, $0.date] }, "case #\(i)")
            } catch PlanSearchError.Rejected(let code, _) {
                guard case .error(let want) = c.expect else { return XCTFail("case #\(i): \(code)") }
                XCTAssertEqual(code, want, "case #\(i)")
            } catch {
                XCTFail("case #\(i): unexpected \(error)")
            }
        }
        XCTAssertEqual(Self.fixtures.planning.count, 66)
    }

    func testFliErrorDoesNotCrash() {
        XCTAssertThrowsError(try fliDecodePage(html: "<html></html>")) { error in
            guard case FliDecodeError.Failed(let code, _) = error else { return XCTFail("\(error)") }
            XCTAssertEqual(code, "schema_changed")
        }
    }
}
