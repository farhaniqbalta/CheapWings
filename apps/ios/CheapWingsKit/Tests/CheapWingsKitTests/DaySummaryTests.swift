import CheapWingsCore
@testable import CheapWingsKit
import XCTest

@MainActor
final class DaySummaryTests: XCTestCase {
    // Synthetic fixtures (not real fares).
    let request = SearchRequest(origins: ["CGK"], destinations: ["DPS"], dateFrom: "2026-12-15",
                                dateThrough: "2026-12-18", currency: "IDR")

    func testDaySummaryLowestPendingFailed() async throws {
        let combos = try request.plan()
        // 15th: two offers; 16th: page unreadable; 17th: cheapest; 18th: never reached (hangs).
        let transport = FakeTransport([page("CGK", "DPS", "2026-12-15", prices: ["1300000", "1250000"]), brokenPage,
                                       page("CGK", "DPS", "2026-12-17", prices: ["990000"])], hangWhenEmpty: true)
        let session = SearchSession(engine: SearchEngine(transport: transport, sleep: FakeClock().sleep), store: nil)
        session.start(request, combos: combos)
        for _ in 0..<300 {
            if case .running(let done, _) = session.phase, done >= 3 { break }
            try await Task.sleep(for: .milliseconds(10))
        }
        let days = DaySummary.make(session)
        XCTAssertEqual(days.map(\.date), ["2026-12-15", "2026-12-16", "2026-12-17", "2026-12-18"])
        XCTAssertEqual(days.map { $0.lowest?.offer.price }, ["1250000", nil, "990000", nil])
        XCTAssertEqual(days.map(\.state), [.searched, .failed("schema_changed"), .searched, .pending])
        XCTAssertEqual(days.map(\.isCheapest), [false, false, true, false])
        session.cancel()
    }

    func testNoFlightsDayIsSearchedNotFailed() {
        let combo = RouteDate(origin: "CGK", destination: "DPS", date: "2026-12-15")
        let days = DaySummary.make(planned: [combo], finished: [combo], offers: [], failures: [])
        XCTAssertEqual(days.first?.state, .searched)
        XCTAssertNil(days.first?.lowest)
        XCTAssertFalse(days.first?.isCheapest ?? true)
    }
}
