import CheapWingsCore
import XCTest

/// P7.4 discovery sources (contracts/fixtures/core/discovery_sources_fixtures.json) through UniFFI.
final class DiscoverySourcesTests: XCTestCase {
    struct ObservationJ: Decodable, Equatable {
        let origin, destination, amount, currency, source_id, fetched_at, price_kind, hidden_city: String
        let departure_date, observed_at, source_reference: String?
    }
    struct FxJ: Decodable { let currency, rate: String }
    struct AnywhereExpect: Decodable {
        let observations: [ObservationJ]?
        let count: Int?
        let first: ObservationJ?
        let unpriced: UInt32?
        let fx: [FxJ]?
        let error: String?
    }
    struct AnywhereCase: Decodable { let name, rpc_json, origin, depart, fetched_at: String; let expect: AnywhereExpect }
    struct QueryJ: Decodable { let origins: [String]; let date_from, date_through, display_currency: String }
    struct CallJ: Decodable { let origin, date: String }
    struct CallsExpect: Decodable { let calls: [CallJ]?; let count: Int?; let error: String? }
    struct CallsCase: Decodable { let name: String; let query: QueryJ; let expect: CallsExpect }
    struct Fixtures: Decodable { let anywhere: [AnywhereCase]; let discovery_calls: [CallsCase] }

    static let fixtures: Fixtures = {
        var url = URL(fileURLWithPath: #filePath)
        for _ in 0..<6 { url.deleteLastPathComponent() }  // → repository root
        let file = url.appendingPathComponent("contracts/fixtures/core/discovery_sources_fixtures.json")
        return try! JSONDecoder().decode(Fixtures.self, from: Data(contentsOf: file))
    }()

    static func plain(_ o: DiscoveryObservation) -> ObservationJ {
        ObservationJ(origin: o.origin, destination: o.destination, amount: o.amount, currency: o.currency,
                     source_id: o.sourceId, fetched_at: o.fetchedAt, price_kind: o.priceKind, hidden_city: o.hiddenCity,
                     departure_date: o.departureDate, observed_at: o.observedAt, source_reference: o.sourceReference)
    }

    func testAnywhereFixtures() {
        XCTAssertEqual(Self.fixtures.anywhere.count, 10)
        for c in Self.fixtures.anywhere {
            do {
                let page = try skiplaggedAnywhere(rpcJson: c.rpc_json, origin: c.origin, depart: c.depart, fetchedAt: c.fetched_at)
                if c.expect.error != nil { XCTFail("\(c.name): expected \(c.expect.error!)"); continue }
                let got = page.observations.map(Self.plain)
                if let all = c.expect.observations { XCTAssertEqual(got, all, c.name) }
                if let n = c.expect.count { XCTAssertEqual(got.count, n, c.name) }
                if c.expect.count != nil { XCTAssertEqual(got.first, c.expect.first, c.name) }
                XCTAssertEqual(page.unpriced, c.expect.unpriced, c.name)
                XCTAssertEqual(page.fx.map { [$0.currency, $0.rate] }, c.expect.fx?.map { [$0.currency, $0.rate] }, c.name)
            } catch SkiplaggedError.Failed(let code, _) {
                XCTAssertEqual(code, c.expect.error, c.name)
            } catch {
                XCTFail("\(c.name): unexpected \(error)")
            }
        }
    }

    func testDiscoveryCallFixtures() {
        for c in Self.fixtures.discovery_calls {
            let q = DiscoveryQuery(origins: c.query.origins, dateFrom: c.query.date_from, dateThrough: c.query.date_through,
                                   displayCurrency: c.query.display_currency, budget: nil, includeHiddenCity: false)
            do {
                let calls = try discoveryCalls(query: q)
                if let want = c.expect.calls { XCTAssertEqual(calls.map { [$0.origin, $0.date] }, want.map { [$0.origin, $0.date] }, c.name) }
                else if let n = c.expect.count { XCTAssertEqual(calls.count, n, c.name) }
                else { XCTFail("\(c.name): expected \(c.expect.error ?? "?")") }
            } catch DiscoveryPlanError.Rejected(let code, _) {
                XCTAssertEqual(code, c.expect.error, c.name)
            } catch {
                XCTFail("\(c.name): unexpected \(error)")
            }
        }
    }
}
