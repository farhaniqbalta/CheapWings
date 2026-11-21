import CheapWingsCore
import XCTest

/// P7 Discover contract (contracts/fixtures/core/discovery_fixtures.json) through the UniFFI Swift API.
final class DiscoveryFixtureTests: XCTestCase {
    struct ObservationJ: Decodable {
        let origin, destination, amount, currency, source_id, fetched_at, price_kind, hidden_city: String
        let departure_date, observed_at, source_reference: String?
    }
    struct QueryJ: Decodable {
        let origins: [String]
        let date_from, date_through, display_currency: String
        let budget: String?
        let include_hidden_city: Bool
    }
    struct FxJ: Decodable { let currency, rate: String }
    struct LeadJ: Decodable { let origin, destination, date, comparable_amount: String; let observation_index: UInt32 }
    struct CountsJ: Decodable {
        let observed, selected, invalid, hidden_city, out_of_window, undated, no_fx, over_budget, superseded, capped: UInt32
    }
    struct ExpectJ: Decodable { let selected: [LeadJ]?; let counts: CountsJ?; let error: String? }
    struct CaseJ: Decodable {
        let name: String
        let query: QueryJ
        let fx: [FxJ]
        let max_route_dates: UInt32
        let observations: [ObservationJ]
        let expect: ExpectJ
    }
    struct Fixtures: Decodable { let cases: [CaseJ] }

    static let fixtures: Fixtures = {
        var url = URL(fileURLWithPath: #filePath)
        for _ in 0..<6 { url.deleteLastPathComponent() }  // → repository root
        let file = url.appendingPathComponent("contracts/fixtures/core/discovery_fixtures.json")
        return try! JSONDecoder().decode(Fixtures.self, from: Data(contentsOf: file))
    }()

    func testDiscoveryFixtures() {
        XCTAssertGreaterThanOrEqual(Self.fixtures.cases.count, 14)
        for c in Self.fixtures.cases {
            let observations = c.observations.map {
                DiscoveryObservation(origin: $0.origin, destination: $0.destination, departureDate: $0.departure_date,
                                     amount: $0.amount, currency: $0.currency, sourceId: $0.source_id,
                                     observedAt: $0.observed_at, fetchedAt: $0.fetched_at, priceKind: $0.price_kind,
                                     hiddenCity: $0.hidden_city, sourceReference: $0.source_reference)
            }
            let query = DiscoveryQuery(origins: c.query.origins, dateFrom: c.query.date_from,
                                       dateThrough: c.query.date_through, displayCurrency: c.query.display_currency,
                                       budget: c.query.budget, includeHiddenCity: c.query.include_hidden_city)
            let fx = c.fx.map { FxRate(currency: $0.currency, rate: $0.rate) }
            do {
                let plan = try selectDiscoveryPlan(observations: observations, query: query, fx: fx,
                                                   maxRouteDates: c.max_route_dates)
                guard let want = c.expect.selected, let n = c.expect.counts else {
                    return XCTFail("\(c.name): expected error \(c.expect.error ?? "?")")
                }
                XCTAssertEqual(plan.selected, want.map {
                    SelectedLead(origin: $0.origin, destination: $0.destination, date: $0.date,
                                 observationIndex: $0.observation_index, comparableAmount: $0.comparable_amount)
                }, c.name)
                XCTAssertEqual(plan.counts, DiscoveryCounts(
                    observed: n.observed, selected: n.selected, invalid: n.invalid, hiddenCity: n.hidden_city,
                    outOfWindow: n.out_of_window, undated: n.undated, noFx: n.no_fx, overBudget: n.over_budget,
                    superseded: n.superseded, capped: n.capped), c.name)
            } catch DiscoveryPlanError.Rejected(let code, _) {
                XCTAssertEqual(code, c.expect.error, c.name)
            } catch {
                XCTFail("\(c.name): unexpected \(error)")
            }
        }
    }
}
