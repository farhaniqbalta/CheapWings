import CheapWingsCore
@testable import CheapWingsKit
import XCTest

/// Discovery outcomes scripted per call date, consumed in order (for retries); records every call.
actor DiscoveryScript {
    private var byDate: [String: [DiscoveryOutcome]]
    private(set) var calls: [String] = []
    init(_ byDate: [String: [DiscoveryOutcome]]) { self.byDate = byDate }
    func next(_ call: DiscoveryCall) -> DiscoveryOutcome {
        calls.append(call.date)
        guard var queue = byDate[call.date], !queue.isEmpty else { return .failed(code: "unscripted") }
        let first = queue.removeFirst()
        byDate[call.date] = queue
        return first
    }
}

struct ScriptedDiscovery: DiscoveryProvider {
    let id = "skiplagged"
    let pacing = ProviderPacing(interval: .seconds(3), maxInFlight: 1)
    let script: DiscoveryScript
    init(_ byDate: [String: [DiscoveryOutcome]]) { script = DiscoveryScript(byDate) }
    func discover(_ call: DiscoveryCall, currency: String, fetchedAt: Date) async -> DiscoveryOutcome {
        await script.next(call)
    }
}

/// Fictitious leads: one USD-priced destination per page, FX 16000 IDR per USD.
func leads(_ date: String, _ pairs: [(String, String)], unpriced: UInt32 = 0) -> DiscoveryOutcome {
    .page(AnywherePage(observations: pairs.map { dest, usd in
        DiscoveryObservation(origin: "CGK", destination: dest, departureDate: date, amount: usd, currency: "USD",
                             sourceId: "skiplagged", observedAt: nil, fetchedAt: "2027-02-20T00:00:00Z",
                             priceKind: "indicative", hiddenCity: "no", sourceReference: nil)
    }, fx: [FxRate(currency: "USD", rate: "16000")], unpriced: unpriced))
}

@MainActor
final class DiscoverySessionTests: XCTestCase {
    let request = SearchRequest(origins: ["CGK"], destinations: [], dateFrom: "2027-03-01", dateThrough: "2027-03-02",
                                currency: "IDR", providers: ["fli"], kind: .discover, budget: nil)
    var dir: URL!
    var clock: FakeClock!

    override func setUp() async throws {
        dir = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        try FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
        clock = FakeClock()
    }

    override func tearDown() async throws {
        try? FileManager.default.removeItem(at: dir)
    }

    func store() throws -> SearchStore { try SearchStore(path: dir.appendingPathComponent("searches.sqlite").path) }

    /// Fli checks: each check on a scripted date finds one offer at `price` (up to 4 per date).
    func checker(_ dates: [String: String]) -> ScriptedProvider {
        ScriptedProvider("fli", pacing: ProviderPacing(interval: .zero, maxInFlight: 1), dates.mapValues { price in
            Array(repeating: ScriptedProvider.found("fli", RouteDate(origin: "CGK", destination: "DPS", date: "2027-03-01"), price: price),
                  count: 4)
        })
    }

    func session(_ discovery: ScriptedDiscovery, checks: ScriptedProvider? = nil, store: SearchPersistence? = nil) -> SearchSession {
        SearchSession(engine: SearchEngine(providers: [checks ?? checker([:])], sleep: clock.sleep), store: store,
                      discovery: discovery, discoverySleep: clock.sleep)
    }

    func waitUntilStopped(_ session: SearchSession) async throws {
        for _ in 0..<300 where session.isRunning { try await Task.sleep(for: .milliseconds(10)) }
        XCTAssertFalse(session.isRunning, "session did not stop: \(session.phase)")
    }

    func testDiscoverThenCheck() async throws {
        let discovery = ScriptedDiscovery(["2027-03-01": [leads("2027-03-01", [("DPS", "46"), ("SIN", "60")])],
                                           "2027-03-02": [leads("2027-03-02", [("DPS", "50")], unpriced: 2)]])
        let session = session(discovery, checks: checker(["2027-03-01": "700000"]))
        try session.startDiscover(request)
        try await waitUntilStopped(session)
        let calls = await discovery.script.calls
        XCTAssertEqual(calls, ["2027-03-01", "2027-03-02"])
        let summary = try XCTUnwrap(session.discovery)
        XCTAssertEqual(summary.callsPlanned, 2)
        XCTAssertEqual(summary.callsDone, 2)
        XCTAssertEqual(summary.callsFailed, 0)
        XCTAssertEqual(summary.unpriced, 2)
        XCTAssertEqual(summary.leads.count, 3)
        XCTAssertEqual(summary.counts?.selected, 2)
        XCTAssertEqual(summary.counts?.superseded, 1)
        XCTAssertEqual(session.planned.map { "\($0.provider) \($0.routeDate.destination) \($0.routeDate.date)" },
                       ["fli DPS 2027-03-01", "fli SIN 2027-03-01"])
        XCTAssertEqual(session.phase, .stopped(.finished))
        XCTAssertEqual(session.offers.count, 2)
        XCTAssertTrue(clock.sleeps.contains(.seconds(3)), "discovery calls are paced")
    }

    func testAllCallsFailedIsUnavailable() async throws {
        let discovery = ScriptedDiscovery(["2027-03-01": [.failed(code: "schema_changed")],
                                           "2027-03-02": [.failed(code: "network")]])
        let session = session(discovery)
        try session.startDiscover(request)
        try await waitUntilStopped(session)
        XCTAssertEqual(session.emptyOutcome, .sourceUnavailable)
        XCTAssertTrue(session.planned.isEmpty)
        XCTAssertEqual(session.discovery?.callsFailed, 2)
    }

    func testNoPricedLeadsIsNoPrices() async throws {
        let discovery = ScriptedDiscovery(["2027-03-01": [leads("2027-03-01", [], unpriced: 4)],
                                           "2027-03-02": [leads("2027-03-02", [])]])
        let session = session(discovery)
        try session.startDiscover(request)
        try await waitUntilStopped(session)
        XCTAssertEqual(session.emptyOutcome, .noPrices)
        XCTAssertEqual(session.discovery?.unpriced, 4)
    }

    func testOverBudgetIsNoneUnderBudget() async throws {
        var tight = request
        tight.budget = "100000"
        let discovery = ScriptedDiscovery(["2027-03-01": [leads("2027-03-01", [("DPS", "46")])],
                                           "2027-03-02": [leads("2027-03-02", [])]])
        let session = session(discovery)
        try session.startDiscover(tight)
        try await waitUntilStopped(session)
        XCTAssertEqual(session.emptyOutcome, .noneUnderBudget)
        XCTAssertEqual(session.discovery?.counts?.overBudget, 1)
    }

    func testPartialDiscoveryPlansFromSurvivors() async throws {
        let discovery = ScriptedDiscovery(["2027-03-01": [.failed(code: "network")],
                                           "2027-03-02": [leads("2027-03-02", [("DPS", "50")])]])
        let session = session(discovery, checks: checker(["2027-03-02": "800000"]))
        try session.startDiscover(request)
        try await waitUntilStopped(session)
        XCTAssertEqual(session.discovery?.callsFailed, 1)
        XCTAssertEqual(session.planned.map(\.routeDate.date), ["2027-03-02"])
        XCTAssertEqual(session.phase, .stopped(.finished))
    }

    func testLongRetryAfterStopsSource() async throws {
        let discovery = ScriptedDiscovery(["2027-03-01": [.retry(after: .seconds(600))]])
        let session = session(discovery)
        try session.startDiscover(request)
        try await waitUntilStopped(session)
        XCTAssertFalse(clock.sleeps.contains(.seconds(600)), "never sleeps out a long Retry-After")
        XCTAssertEqual(session.providerStops["skiplagged"]?.reason, .rateLimited)
        let calls = await discovery.script.calls
        XCTAssertEqual(calls, ["2027-03-01"], "the source stops: no further calls")
        XCTAssertEqual(session.emptyOutcome, .sourceUnavailable)
    }

    func testShortRetryAfterRetriesThenContinues() async throws {
        let discovery = ScriptedDiscovery(["2027-03-01": [.retry(after: .seconds(5)), leads("2027-03-01", [("DPS", "46")])],
                                           "2027-03-02": [leads("2027-03-02", [])]])
        let session = session(discovery, checks: checker(["2027-03-01": "700000"]))
        try session.startDiscover(request)
        try await waitUntilStopped(session)
        XCTAssertTrue(clock.sleeps.contains(.seconds(5)))
        XCTAssertEqual(session.discovery?.callsFailed, 0)
        XCTAssertEqual(session.planned.count, 1)
    }

    func testForbiddenKeepsLeadsSoFar() async throws {
        let discovery = ScriptedDiscovery(["2027-03-01": [leads("2027-03-01", [("DPS", "46")])],
                                           "2027-03-02": [.stop(.blocked("http_403"))]])
        let session = session(discovery, checks: checker(["2027-03-01": "700000"]))
        try session.startDiscover(request)
        try await waitUntilStopped(session)
        XCTAssertEqual(session.providerStops["skiplagged"]?.reason, .blocked("http_403"))
        XCTAssertEqual(session.discovery?.callsFailed, 1)
        XCTAssertEqual(session.planned.count, 1)
    }

    func testCancelDuringDiscoveryCommitsNothing() async throws {
        let discovery = ScriptedDiscovery(["2027-03-01": [leads("2027-03-01", [("DPS", "46")])]])
        let store = try store()
        let session = SearchSession(engine: SearchEngine(providers: [checker([:])], sleep: clock.sleep), store: store,
                                    discovery: discovery, discoverySleep: { _ in try await Task.sleep(for: .seconds(30)) })
        try session.startDiscover(request)
        for _ in 0..<100 where await discovery.script.calls.isEmpty { try await Task.sleep(for: .milliseconds(5)) }
        session.cancel()
        XCTAssertEqual(session.phase, .stopped(.cancelled))
        let stored = try XCTUnwrap(try store.latest())
        XCTAssertEqual(stored.stage, "discovering")
        XCTAssertNil(stored.discovery)
        XCTAssertTrue(stored.combos.isEmpty)
    }

    func testRestartDuringDiscoveryReruns() async throws {
        let store = try store()
        _ = try store.createDiscovery(request: request.stored, nowMs: 1)  // app killed mid-discovery
        let discovery = ScriptedDiscovery(["2027-03-01": [leads("2027-03-01", [("DPS", "46")])],
                                           "2027-03-02": [leads("2027-03-02", [])]])
        let session = session(discovery, checks: checker(["2027-03-01": "700000"]), store: store)
        session.restoreLatest()
        XCTAssertEqual(session.phase, .stopped(.interrupted))
        XCTAssertTrue(session.canResume)
        session.resume()
        try await waitUntilStopped(session)
        let calls = await discovery.script.calls
        XCTAssertEqual(calls, ["2027-03-01", "2027-03-02"])
        let stored = try XCTUnwrap(try store.latest())
        XCTAssertEqual(stored.stage, "checking")
        XCTAssertEqual(stored.combos.count, 1)
        XCTAssertEqual(session.offers.count, 1)
    }

    func testRestartAfterCommitResumesItems() async throws {
        let store = try store()
        let id = try store.createDiscovery(request: request.stored, nowMs: 1)
        guard case .page(let page) = leads("2027-03-01", [("DPS", "46")]) else { return XCTFail() }
        let item = WorkItem(provider: "fli", routeDate: RouteDate(origin: "CGK", destination: "DPS", date: "2027-03-01"))
        try store.commitDiscovery(searchId: id, snapshot: DiscoverySnapshot(observations: page.observations, fx: page.fx,
                                                                            callsPlanned: 2, callsFailed: 0, unpriced: 0),
                                  items: [item], nowMs: 2)
        let discovery = ScriptedDiscovery([:])
        let session = session(discovery, checks: checker(["2027-03-01": "700000"]), store: store)
        session.restoreLatest()
        XCTAssertEqual(session.discovery?.counts?.selected, 1, "counts recomputed from the snapshot")
        XCTAssertTrue(session.canResume)
        session.resume()
        try await waitUntilStopped(session)
        let calls = await discovery.script.calls
        XCTAssertTrue(calls.isEmpty, "a committed discovery is never re-run")
        XCTAssertEqual(try store.latest()?.combos.count, 1)
        XCTAssertEqual(session.offers.count, 1)
    }

    func testBackgroundPauseBetweenCalls() async throws {
        let discovery = ScriptedDiscovery(["2027-03-01": [leads("2027-03-01", [("DPS", "46")])],
                                           "2027-03-02": [leads("2027-03-02", [])]])
        let session = session(discovery)
        try session.startDiscover(request)
        session.pauseAfterCurrentRequest()
        try await waitUntilStopped(session)
        XCTAssertEqual(session.phase, .stopped(.backgrounded))
        let calls = await discovery.script.calls
        XCTAssertEqual(calls, ["2027-03-01"])
        XCTAssertTrue(session.canResume)
    }

    func testInvalidQueryThrows() {
        var bad = request
        bad.dateThrough = "2027-04-30"
        XCTAssertThrowsError(try session(ScriptedDiscovery([:])).startDiscover(bad))
    }

    // Final review: a stopped only checker is not "no flights"; a pause on the last call keeps the run.

    func testStoppedOnlyCheckerIsUnavailable() async throws {
        var skiplaggedOnly = request
        skiplaggedOnly.providers = ["skiplagged"]
        let discovery = ScriptedDiscovery(["2027-03-01": [leads("2027-03-01", [("DPS", "46")])],
                                           "2027-03-02": [.stop(.blocked("http_403"))]])
        let session = session(discovery)
        try session.startDiscover(skiplaggedOnly)
        try await waitUntilStopped(session)
        XCTAssertEqual(session.discovery?.counts?.selected, 1)
        XCTAssertTrue(session.planned.isEmpty)
        XCTAssertEqual(session.emptyOutcome, .sourceUnavailable)
    }

    func testPauseOnLastCallCommitsThenResumesChecks() async throws {
        var oneDay = request
        oneDay.dateThrough = "2027-03-01"
        let store = try store()
        let discovery = ScriptedDiscovery(["2027-03-01": [leads("2027-03-01", [("DPS", "46")])]])
        let session = session(discovery, checks: checker(["2027-03-01": "700000"]), store: store)
        try session.startDiscover(oneDay)
        session.pauseAfterCurrentRequest()
        try await waitUntilStopped(session)
        XCTAssertEqual(session.phase, .stopped(.backgrounded))
        XCTAssertEqual(session.discovery?.committed, true)
        XCTAssertEqual(try store.latest()?.stage, "checking")
        XCTAssertTrue(session.canResume)
        session.resume()
        try await waitUntilStopped(session)
        XCTAssertEqual(session.offers.count, 1)
        let calls = await discovery.script.calls
        XCTAssertEqual(calls, ["2027-03-01"], "resume runs the checks, not discovery again")
    }
}
