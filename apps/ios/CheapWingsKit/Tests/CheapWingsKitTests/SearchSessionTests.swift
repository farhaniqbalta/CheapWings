import CheapWingsCore
@testable import CheapWingsKit
import XCTest

@MainActor
final class SearchSessionTests: XCTestCase {
    let request = SearchRequest(origins: ["CGK"], destinations: ["DPS"], dateFrom: "2026-12-15",
                                dateThrough: "2026-12-15", currency: "IDR")
    let noPrices = FetchedPage(status: 200, body: Data("<script>AF_initDataCallback({key: 'ds:1', hash: '2', data:[null,null,[[]],null], sideChannel: {}});</script>".utf8), refusedRedirect: nil)

    func session(_ transport: FakeTransport) -> SearchSession {
        SearchSession(engine: SearchEngine(transport: transport, sleep: FakeClock().sleep))
    }

    func waitUntilStopped(_ session: SearchSession) async throws {
        for _ in 0..<200 where session.isRunning { try await Task.sleep(for: .milliseconds(10)) }
        XCTAssertFalse(session.isRunning, "search did not stop")
    }

    func testCancelThenStartDoesNotCancelTheNewSearch() async throws {
        // Both searches hang in their request, so the new one must still be running after the
        // old one's loop has wound down; otherwise Search re-enables and a second engine can run.
        let transport = FakeTransport([], hangOnFetch: true)
        let session = session(transport)
        let combos = try request.plan()
        session.start(request, combos: combos)
        try await Task.sleep(for: .milliseconds(50))
        session.cancel()
        session.start(request, combos: combos)
        try await Task.sleep(for: .milliseconds(150))  // let the old search's loop wind down
        XCTAssertTrue(session.isRunning, "new search was marked stopped: \(session.phase)")
        session.cancel()
    }

    func testStartingAgainCancelsThePreviousSearch() async throws {
        // Never two engines at once: that would break one-request-at-a-time pacing.
        let transport = FakeTransport([], hangOnFetch: true)
        let session = session(transport)
        let combos = try request.plan()
        session.start(request, combos: combos)
        try await Task.sleep(for: .milliseconds(50))
        session.start(request, combos: combos)
        try await Task.sleep(for: .milliseconds(100))
        let cancelled = await transport.cancelledFetches
        XCTAssertEqual(cancelled, 1, "the first search's request must be cancelled")
        XCTAssertTrue(session.isRunning)
        session.cancel()
    }

    func testNoOffersArriveAfterCancel() async throws {
        let transport = FakeTransport([page("CGK", "DPS", "2026-12-15", prices: ["1"])], hangOnFetch: true)
        let session = session(transport)
        session.start(request, combos: try request.plan())
        try await Task.sleep(for: .milliseconds(50))
        session.cancel()
        try await Task.sleep(for: .milliseconds(100))
        XCTAssertEqual(session.phase, .stopped(.cancelled))
        XCTAssertTrue(session.offers.isEmpty)
    }

    func testFormatChangedOnlyWhenEveryFailureIsADecodeFailure() async throws {
        let session = session(FakeTransport([brokenPage]))
        session.start(request, combos: try request.plan())
        try await waitUntilStopped(session)
        XCTAssertEqual(session.emptyOutcome, .formatChanged)
    }

    func testOfflineIsNotReportedAsFormatChanged() async throws {
        let session = session(FakeTransport(results: [.failure(URLError(.notConnectedToInternet))]))
        session.start(request, combos: try request.plan())
        try await waitUntilStopped(session)
        // P5.6: offline pauses the search (Resume later) instead of failing route/dates.
        XCTAssertEqual(session.phase, .stopped(.offline))
        XCTAssertNotEqual(session.emptyOutcome, .formatChanged)
        XCTAssertTrue(session.failures.isEmpty)
    }

    func testTimeoutsStillReportSearchesFailed() async throws {
        let session = session(FakeTransport(results: [.failure(URLError(.timedOut))]))
        session.start(request, combos: try request.plan())
        try await waitUntilStopped(session)
        XCTAssertEqual(session.emptyOutcome, .searchesFailed(1))
        XCTAssertEqual(session.failures.map(\.code), ["network"])
    }

    func testFinishedWithNothingFoundSaysNoFlights() async throws {
        let session = session(FakeTransport([noPrices]))
        session.start(request, combos: try request.plan())
        try await waitUntilStopped(session)
        XCTAssertEqual(session.emptyOutcome, .noFlights)
    }

    func testHiddenOffersAreCountedNotSilentlyLost() async throws {
        let html = String(decoding: page("CGK", "DPS", "2026-12-15", prices: ["1250000", "4161210"]).body, as: UTF8.self)
        let patched = html.replacingCharacters(in: html.range(of: "\"GgUaA0lEUg\"", options: .backwards)!, with: "null")
        let session = session(FakeTransport([FetchedPage(status: 200, body: Data(patched.utf8), refusedRedirect: nil)]))
        session.start(request, combos: try request.plan())
        try await waitUntilStopped(session)
        XCTAssertEqual(session.offers.count, 1)
        XCTAssertEqual(session.hiddenOffers, ["currency None": 1])
    }

    func testResultsKeepTheCurrencyOfTheSearchThatRan() async throws {
        let session = session(FakeTransport([page("CGK", "DPS", "2026-12-15", prices: ["1250000"])]))
        session.start(request, combos: try request.plan())
        try await waitUntilStopped(session)
        XCTAssertEqual(session.currency, "IDR")
        XCTAssertNil(session.emptyOutcome)
    }
}
