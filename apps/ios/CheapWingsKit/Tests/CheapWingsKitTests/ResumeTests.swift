import CheapWingsCore
@testable import CheapWingsKit
import XCTest

/// Persistence whose every call fails (full disk, corrupt file after open, …).
final class ThrowingStore: SearchPersistence, @unchecked Sendable {
    struct Broken: Error {}
    func createSearch(request: StoredRequest, items: [WorkItem], nowMs: Int64) throws -> Int64 { throw Broken() }
    func setProviderStopped(searchId: Int64, provider: String, reason: String, nowMs: Int64) throws { throw Broken() }
    func finishCombo(searchId: Int64, index: UInt32, offers: [SourceOffer], hidden: [String], failure: String?, nowMs: Int64) throws { throw Broken() }
    func setStopped(searchId: Int64, reason: String, nowMs: Int64) throws { throw Broken() }
    func clearStopped(searchId: Int64) throws { throw Broken() }
    func latest() throws -> StoredSearch? { throw Broken() }
    func pending(searchId: Int64) throws -> [StoredCombo] { throw Broken() }
}

@MainActor
final class ResumeTests: XCTestCase {
    let request = SearchRequest(origins: ["CGK"], destinations: ["DPS"], dateFrom: "2026-12-15",
                                dateThrough: "2026-12-17", currency: "IDR")
    var dir: URL!

    override func setUp() async throws {
        dir = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        try FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
    }

    override func tearDown() async throws {
        try? FileManager.default.removeItem(at: dir)
    }

    func store() throws -> SearchStore { try SearchStore(path: dir.appendingPathComponent("searches.sqlite").path) }

    func session(_ transport: FakeTransport, store: SearchPersistence?, now: @escaping @Sendable () -> Date = { Date() }) -> SearchSession {
        SearchSession(engine: SearchEngine(transport: transport, maxInFlight: 1, sleep: FakeClock().sleep), store: store, now: now)
    }

    func waitUntilStopped(_ session: SearchSession) async throws {
        for _ in 0..<300 where session.isRunning { try await Task.sleep(for: .milliseconds(10)) }
        XCTAssertFalse(session.isRunning, "search did not stop")
    }

    func waitForDone(_ session: SearchSession, _ done: Int) async throws {
        for _ in 0..<300 {
            if case .running(let d, _) = session.phase, d >= done { return }
            try await Task.sleep(for: .milliseconds(10))
        }
        XCTFail("never reached \(done) done: \(session.phase)")
    }

    /// Runs dates 1–2 of 3, then the app "dies" during date 3 (request hangs, session stopped).
    func interruptedAfterTwo() async throws -> SearchStore {
        let store = try store()
        let first = session(FakeTransport([page("CGK", "DPS", "2026-12-15", prices: ["1250000"]),
                                           page("CGK", "DPS", "2026-12-16", prices: ["1300000"])], hangWhenEmpty: true), store: store)
        first.start(request, combos: try request.plan())
        try await waitForDone(first, 2)
        first.stopForBackground()  // date 3 never finished
        return store
    }

    func testCheckpointsEachFinishedRouteDate() async throws {
        let store = try await interruptedAfterTwo()
        let fresh = session(FakeTransport([]), store: store)
        fresh.restoreLatest()
        XCTAssertEqual(Set(fresh.offers.map(\.routeDate.date)), ["2026-12-15", "2026-12-16"])
        XCTAssertEqual(fresh.resumable?.done, 2)
        XCTAssertEqual(fresh.resumable?.total, 3)
        XCTAssertEqual(fresh.phase, .stopped(.backgrounded))
    }

    func testResumeFetchesOnlyPending() async throws {
        let store = try await interruptedAfterTwo()
        let transport = FakeTransport([page("CGK", "DPS", "2026-12-17", prices: ["1100000"])])
        let fresh = session(transport, store: store)
        fresh.restoreLatest()
        XCTAssertTrue(fresh.canResume)
        fresh.resume()
        try await waitUntilStopped(fresh)
        let fetched = await transport.fetched
        XCTAssertEqual(fetched.count, 1)
        XCTAssertTrue(fetched[0].absoluteString.contains(Tfs.forTesting("CGK", "DPS", "2026-12-17")))
        XCTAssertEqual(fresh.phase, .stopped(.finished))
        XCTAssertEqual(fresh.offers.map(\.offer.priceOriginal), ["1100000", "1250000", "1300000"])
        XCTAssertNil(fresh.resumable, "nothing left to resume")
    }

    func testResumeUsesStoredRequestNotForm() async throws {
        let store = try await interruptedAfterTwo()
        let transport = FakeTransport([page("CGK", "DPS", "2026-12-17", prices: ["1100000"])])
        let fresh = session(transport, store: store)
        fresh.restoreLatest()
        XCTAssertEqual(fresh.resumable?.request, request)
        fresh.resume()
        try await waitUntilStopped(fresh)
        let url = await transport.fetched.first?.absoluteString ?? ""
        XCTAssertTrue(url.contains("curr=IDR") && url.contains("gl=ID"), url)
    }

    func testBlockedStopDoesNotOfferImmediateResume() async throws {
        let store = try store()
        let forbidden = FetchedPage(status: 403, body: Data(), refusedRedirect: nil)
        let blocked = session(FakeTransport([page("CGK", "DPS", "2026-12-15", prices: ["1"]), forbidden]), store: store)
        blocked.start(request, combos: try request.plan())
        try await waitUntilStopped(blocked)
        XCTAssertEqual(blocked.phase, .stopped(.blocked("http_403")))

        let stoppedAt = Date()
        let soon = session(FakeTransport([]), store: store, now: { stoppedAt.addingTimeInterval(5 * 60) })
        soon.restoreLatest()
        XCTAssertFalse(soon.canResume)
        XCTAssertNotNil(soon.resumeAllowedAfter)
        let later = session(FakeTransport([]), store: store, now: { stoppedAt.addingTimeInterval(31 * 60) })
        later.restoreLatest()
        XCTAssertTrue(later.canResume)
    }

    func testOfflineStopResumesPendingWithoutCooldown() async throws {
        let store = try store()
        let first = session(FakeTransport(results: [.success(page("CGK", "DPS", "2026-12-15", prices: ["1250000"])),
                                                    .failure(URLError(.networkConnectionLost))]), store: store)
        first.start(request, combos: try request.plan())
        try await waitUntilStopped(first)
        XCTAssertEqual(first.phase, .stopped(.offline))
        XCTAssertTrue(first.failures.isEmpty)

        let transport = FakeTransport([page("CGK", "DPS", "2026-12-16", prices: ["1300000"]),
                                       page("CGK", "DPS", "2026-12-17", prices: ["1100000"])])
        let fresh = session(transport, store: store)
        fresh.restoreLatest()
        XCTAssertEqual(fresh.resumable?.done, 1)
        XCTAssertTrue(fresh.canResume, "no Google cooldown after a lost connection")
        fresh.resume()
        try await waitUntilStopped(fresh)
        let fetched = await transport.fetched
        XCTAssertEqual(fetched.count, 2)
        XCTAssertEqual(fresh.phase, .stopped(.finished))
    }

    func testParallelStopLeavesUnreleasedPendingForResume() async throws {
        let store = try store()
        let five = SearchRequest(origins: ["CGK"], destinations: ["DPS"], dateFrom: "2026-12-15",
                                 dateThrough: "2026-12-19", currency: "IDR")
        let combos = try five.plan()
        var outcomes: [URL: GateTransport.Outcome] = [:]
        for (i, combo) in combos.enumerated() {
            outcomes[five.searchURL(combo)] = i == 1
                ? .page(FetchedPage(status: 429, body: Data(), refusedRedirect: nil))
                : .page(page("CGK", "DPS", combo.date, prices: ["\(1_000_000 + i)"]))
        }
        let gate = GateTransport(outcomes)
        let first = SearchSession(engine: SearchEngine(transport: gate, maxInFlight: 3, sleep: FakeClock().sleep), store: store)
        first.start(five, combos: combos)
        for _ in 0..<300 where await gate.started.count < 3 { try await Task.sleep(for: .milliseconds(5)) }
        for i in [2, 0, 1] {  // 3 replies first (buffered), then 1, then the 429 on 2
            await gate.release(five.searchURL(combos[i]))
            try await Task.sleep(for: .milliseconds(10))
        }
        try await waitUntilStopped(first)
        XCTAssertEqual(first.phase, .stopped(.rateLimited))
        XCTAssertEqual(try store.pending(searchId: try XCTUnwrap(store.latest()).id).map(\.routeDate), Array(combos[1...]))

        let stoppedAt = Date()
        let transport = FakeTransport(combos[1...].map { page("CGK", "DPS", $0.date, prices: ["900000"]) })
        let later = SearchSession(engine: SearchEngine(transport: transport, maxInFlight: 1, sleep: FakeClock().sleep),
                                  store: store, now: { stoppedAt.addingTimeInterval(31 * 60) })
        later.restoreLatest()
        XCTAssertTrue(later.canResume)
        later.resume()
        try await waitUntilStopped(later)
        let fetched = await transport.fetched.count
        XCTAssertEqual(fetched, 4)
        XCTAssertEqual(later.phase, .stopped(.finished))
    }

    func testOfflineStoredTextRoundTrips() {
        XCTAssertEqual(StopReason.offline.storedText, "offline")
        XCTAssertEqual(StopReason(storedText: "offline"), .offline)
        XCTAssertFalse(StopReason.offline.isProviderStop)
    }

    func testDoubleResumeNeverRunsTwoEngines() async throws {
        let store = try await interruptedAfterTwo()
        let transport = FakeTransport([], hangOnFetch: true)
        let fresh = session(transport, store: store)
        fresh.restoreLatest()
        fresh.resume()
        try await Task.sleep(for: .milliseconds(50))
        fresh.resume()  // a double tap while resuming is ignored
        try await Task.sleep(for: .milliseconds(100))
        let fetched = await transport.fetched.count
        let cancelled = await transport.cancelledFetches
        XCTAssertEqual(fetched, 1)
        XCTAssertEqual(cancelled, 0)
        XCTAssertTrue(fresh.isRunning)
        fresh.cancel()
    }

    func testStoreFailureDoesNotStopSearch() async throws {
        let s = session(FakeTransport([page("CGK", "DPS", "2026-12-15", prices: ["1250000"]),
                                       page("CGK", "DPS", "2026-12-16", prices: ["1300000"]),
                                       page("CGK", "DPS", "2026-12-17", prices: ["1100000"])]), store: ThrowingStore())
        s.start(request, combos: try request.plan())
        try await waitUntilStopped(s)
        XCTAssertEqual(s.offers.count, 3)
        XCTAssertEqual(s.phase, .stopped(.finished))
        XCTAssertNotNil(s.storeError)
    }

    /// Without working history, Resume must still work (from memory) instead of a dead button.
    func resumeWithoutHistory(_ store: SearchPersistence?) async throws {
        let transport = FakeTransport([page("CGK", "DPS", "2026-12-15", prices: ["1250000"]),
                                       page("CGK", "DPS", "2026-12-16", prices: ["1300000"])], hangWhenEmpty: true)
        let s = session(transport, store: store)
        s.start(request, combos: try request.plan())
        try await waitForDone(s, 2)
        s.stopForBackground()
        XCTAssertTrue(s.canResume)
        s.resume()
        try await Task.sleep(for: .milliseconds(100))
        let fetched = await transport.fetched
        XCTAssertEqual(fetched.count, 4, "date 3 interrupted, then re-fetched once on resume")
        XCTAssertTrue(fetched[3].absoluteString.contains(Tfs.forTesting("CGK", "DPS", "2026-12-17")))
        XCTAssertTrue(s.isRunning)
        s.cancel()
    }

    func testResumeWorksWithoutAStore() async throws {
        try await resumeWithoutHistory(nil)
    }

    func testResumeWorksWhenTheStoreFails() async throws {
        try await resumeWithoutHistory(ThrowingStore())
    }

    func testStaleOffersAreFlagged() throws {
        let combo = try request.plan()[0]
        let offer = sourceOffer("fli", combo.date, price: "1")
        let old = FoundOffer(routeDate: combo, index: 0, offer: offer, searchURL: URL(string: "https://example.invalid")!,
                             fetchedAt: Date().addingTimeInterval(-61 * 60))
        let fresh = FoundOffer(routeDate: combo, index: 0, offer: offer, searchURL: URL(string: "https://example.invalid")!)
        XCTAssertTrue(old.isStale)
        XCTAssertFalse(fresh.isStale)
    }
}

/// tfs value the core builds for a route/date (to recognise which page was requested).
enum Tfs {
    static func forTesting(_ origin: String, _ destination: String, _ date: String) -> String {
        let url = fliSearchUrl(origin: origin, destination: destination, date: date, currency: "IDR", country: "ID")
        return String(url.split(separator: "?")[1].split(separator: "&")[0])
    }
}
