import CheapWingsCore
@testable import CheapWingsKit
import XCTest

/// A neutral offer for tests (synthetic fares).
func sourceOffer(_ provider: String, _ date: String, price: String, comparable: String? = nil, legs: [FliLeg] = []) -> SourceOffer {
    SourceOffer(provider: provider, id: "\(provider)-\(date)-\(price)", origin: "CGK", destination: "DPS",
                departLocal: "\(date)T07:00", arriveLocal: "\(date)T09:55", minutes: 115, stops: 0,
                carriers: provider == "fli" ? ["GA"] : ["Garuda Indonesia"], legs: legs,
                priceOriginal: price, currencyOriginal: provider == "fli" ? "IDR" : "USD",
                priceComparable: comparable ?? price, fx: nil, link: nil, hiddenCity: provider == "fli" ? "unknown" : "no")
}

/// Provider whose outcomes are scripted per date (consumed in order, for retries); `nil` script
/// entries mean "hang until cancelled".
actor OutcomeScript {
    private var byDate: [String: [ProviderOutcome?]]
    private(set) var calls: [String] = []
    init(_ byDate: [String: [ProviderOutcome?]]) { self.byDate = byDate }
    func next(_ date: String) -> ProviderOutcome?? {
        calls.append(date)
        guard var queue = byDate[date], !queue.isEmpty else { return .none }
        let first = queue.removeFirst()
        byDate[date] = queue
        return .some(first)
    }
}

struct ScriptedProvider: SearchProvider {
    let id: String
    let pacing: ProviderPacing
    let script: OutcomeScript

    init(_ id: String, pacing: ProviderPacing, _ byDate: [String: [ProviderOutcome?]]) {
        self.id = id
        self.pacing = pacing
        script = OutcomeScript(byDate)
    }

    func search(_ combo: RouteDate, request: SearchRequest) async -> ProviderOutcome {
        let scripted = await script.next(combo.date)
        guard case .some(.some(let outcome)) = scripted else {
            do { try await Task.sleep(for: .seconds(30)) } catch { return .stop(.cancelled) }
            return .stop(.cancelled)
        }
        return outcome
    }

    static func found(_ provider: String, _ combo: RouteDate, price: String, comparable: String? = nil) -> ProviderOutcome {
        .found(offers: [FoundOffer(routeDate: combo, index: 0, offer: sourceOffer(provider, combo.date, price: price, comparable: comparable),
                                   searchURL: URL(string: "https://example.invalid")!)], hidden: [])
    }
}

final class ProviderLanesTests: XCTestCase {
    let request = SearchRequest(origins: ["CGK"], destinations: ["DPS"], dateFrom: "2026-12-15",
                                dateThrough: "2026-12-16", currency: "IDR", providers: ["fli", "skiplagged"])
    var combos: [RouteDate] { try! request.plan() }
    var items: [WorkItem] { combos.flatMap { c in ["fli", "skiplagged"].map { WorkItem(provider: $0, routeDate: c) } } }
    let fast = ProviderPacing(interval: .milliseconds(250), maxInFlight: 2)
    let slow = ProviderPacing(interval: .seconds(3), maxInFlight: 1)

    func collect(_ engine: SearchEngine) async -> [SearchEvent] {
        var events: [SearchEvent] = []
        for await e in engine.run(request, items: items) { events.append(e) }
        return events
    }

    func offerProviders(_ events: [SearchEvent]) -> [String] {
        events.flatMap { if case .offers(let o) = $0 { return o.map(\.offer.provider) } else { return [] } }
    }

    func stop(_ events: [SearchEvent]) -> StopReason? {
        events.compactMap { if case .stopped(let r) = $0 { return r } else { return nil } }.last
    }

    func testTwoProvidersRunSideBySideEachPaced() async {
        let c = combos
        let fli = ScriptedProvider("fli", pacing: fast, [c[0].date: [ScriptedProvider.found("fli", c[0], price: "1")],
                                                        c[1].date: [ScriptedProvider.found("fli", c[1], price: "2")]])
        let skip = ScriptedProvider("skiplagged", pacing: slow, [c[0].date: [ScriptedProvider.found("skiplagged", c[0], price: "3")],
                                                                c[1].date: [ScriptedProvider.found("skiplagged", c[1], price: "4")]])
        let clock = FakeClock()
        let events = await collect(SearchEngine(providers: [fli, skip], sleep: clock.sleep))
        XCTAssertEqual(Set(offerProviders(events)), ["fli", "skiplagged"])
        XCTAssertEqual(offerProviders(events).count, 4)
        XCTAssertEqual(clock.sleeps.sorted(), [.milliseconds(250), .seconds(3)])
        XCTAssertEqual(events.compactMap { if case .progress(let d, _) = $0 { return d } else { return nil } }, [1, 2, 3, 4])
        XCTAssertEqual(stop(events), .finished)
    }

    func testItemEventsAreAtomic() async {
        let c = combos
        let fli = ScriptedProvider("fli", pacing: fast, [c[0].date: [ScriptedProvider.found("fli", c[0], price: "1")],
                                                        c[1].date: [ScriptedProvider.found("fli", c[1], price: "2")]])
        let skip = ScriptedProvider("skiplagged", pacing: fast, [c[0].date: [ScriptedProvider.found("skiplagged", c[0], price: "3")],
                                                                c[1].date: [ScriptedProvider.found("skiplagged", c[1], price: "4")]])
        let events = await collect(SearchEngine(providers: [fli, skip], sleep: FakeClock().sleep))
        var current: Int?
        for event in events {
            switch event {
            case .item(let i): current = i
            case .offers(let found):
                let item = items[current!]
                XCTAssertEqual(found.map(\.offer.provider), [item.provider])
                XCTAssertEqual(found.map(\.routeDate), [item.routeDate])
            default: break
            }
        }
    }

    func testRetryAfterThenSuccess() async {
        let c = combos
        let skip = ScriptedProvider("skiplagged", pacing: slow, [c[0].date: [.retry(after: .seconds(30)), ScriptedProvider.found("skiplagged", c[0], price: "3")],
                                                                c[1].date: [ScriptedProvider.found("skiplagged", c[1], price: "4")]])
        let fli = ScriptedProvider("fli", pacing: fast, [c[0].date: [ScriptedProvider.found("fli", c[0], price: "1")],
                                                        c[1].date: [ScriptedProvider.found("fli", c[1], price: "2")]])
        let clock = FakeClock()
        let events = await collect(SearchEngine(providers: [fli, skip], sleep: clock.sleep))
        XCTAssertTrue(clock.sleeps.contains(.seconds(30)))
        XCTAssertEqual(offerProviders(events).filter { $0 == "skiplagged" }.count, 2)
        XCTAssertFalse(events.contains { if case .comboFailed = $0 { return true } else { return false } })
        XCTAssertEqual(stop(events), .finished)
    }

    func testRetryGivesUpAfterThreeAttempts() async {
        let c = combos
        let limited = ProviderOutcome.retry(after: .seconds(15))
        let skip = ScriptedProvider("skiplagged", pacing: slow, [c[0].date: [limited, limited, limited],
                                                                c[1].date: [ScriptedProvider.found("skiplagged", c[1], price: "4")]])
        let fli = ScriptedProvider("fli", pacing: fast, [c[0].date: [ScriptedProvider.found("fli", c[0], price: "1")],
                                                        c[1].date: [ScriptedProvider.found("fli", c[1], price: "2")]])
        let events = await collect(SearchEngine(providers: [fli, skip], sleep: FakeClock().sleep))
        let failed = events.compactMap { if case .comboFailed(let rd, let code) = $0 { return "\(rd.date) \(code)" } else { return nil } }
        XCTAssertEqual(failed, ["\(c[0].date) http_rate_limited"])
        let calls = await skip.script.calls
        XCTAssertEqual(calls.filter { $0 == c[0].date }.count, 3)
        XCTAssertEqual(offerProviders(events).filter { $0 == "fli" }.count, 2)
    }

    func testLaneStopOnlyStopsThatProvider() async {
        let c = combos
        let fli = ScriptedProvider("fli", pacing: ProviderPacing(interval: .milliseconds(250), maxInFlight: 1),
                                   [c[0].date: [.stop(.blocked("http_403"))]])
        let skip = ScriptedProvider("skiplagged", pacing: slow, [c[0].date: [ScriptedProvider.found("skiplagged", c[0], price: "3")],
                                                                c[1].date: [ScriptedProvider.found("skiplagged", c[1], price: "4")]])
        let events = await collect(SearchEngine(providers: [fli, skip], sleep: FakeClock().sleep))
        XCTAssertTrue(events.contains { if case .providerStopped("fli", .blocked("http_403")) = $0 { return true } else { return false } })
        XCTAssertEqual(offerProviders(events), ["skiplagged", "skiplagged"])
        XCTAssertEqual(stop(events), .blocked("http_403"))
        let fliCalls = await fli.script.calls
        XCTAssertEqual(fliCalls, [c[0].date], "no Fli request after its stop")
    }

    func testOfflineStopsEveryLane() async {
        let c = combos
        let fli = ScriptedProvider("fli", pacing: fast, [c[0].date: [nil], c[1].date: [nil]])  // hang
        let skip = ScriptedProvider("skiplagged", pacing: slow, [c[0].date: [.stop(.offline)]])
        let events = await collect(SearchEngine(providers: [fli, skip], sleep: FakeClock().sleep))
        XCTAssertEqual(stop(events), .offline)
        XCTAssertFalse(events.contains { if case .comboFailed = $0 { return true } else { return false } })
    }

    func testUnconvertedPriceIsNeverCheapest() {
        let c = combos
        let usdOnly = FoundOffer(routeDate: c[0], index: 0, offer: sourceOffer("skiplagged", c[0].date, price: "10", comparable: nil),
                                 searchURL: URL(string: "https://example.invalid")!)
        let idr = FoundOffer(routeDate: c[0], index: 0, offer: sourceOffer("fli", c[0].date, price: "1500000"),
                             searchURL: URL(string: "https://example.invalid")!)
        let ranked = rankLowestAdvertised([usdOnly, idr])
        XCTAssertEqual(ranked.map(\.offer.provider), ["fli", "skiplagged"], "unconverted offers rank after comparable ones")
        XCTAssertTrue(DaySummary.isLowest(idr, among: ranked))
        XCTAssertFalse(DaySummary.isLowest(usdOnly, among: ranked))
    }

    func testDayIsPendingUntilEverySourceIsDone() {
        let c = combos
        let fliItem = WorkItem(provider: "fli", routeDate: c[0])
        let skipItem = WorkItem(provider: "skiplagged", routeDate: c[0])
        let days = DaySummary.make(planned: [fliItem, skipItem], finished: [fliItem], offers: [], failures: [])
        XCTAssertEqual(days.first?.state, .pending)
        let done = DaySummary.make(planned: [fliItem, skipItem], finished: [fliItem, skipItem], offers: [], failures: [])
        XCTAssertEqual(done.first?.state, .searched)
    }
}

@MainActor
final class ProviderResumeTests: XCTestCase {
    let request = SearchRequest(origins: ["CGK"], destinations: ["DPS"], dateFrom: "2026-12-15",
                                dateThrough: "2026-12-16", currency: "IDR", providers: ["fli", "skiplagged"])
    var dir: URL!

    override func setUp() async throws {
        dir = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        try FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
    }

    override func tearDown() async throws { try? FileManager.default.removeItem(at: dir) }

    func store() throws -> SearchStore { try SearchStore(path: dir.appendingPathComponent("searches.sqlite").path) }

    func waitUntilStopped(_ session: SearchSession) async throws {
        for _ in 0..<300 where session.isRunning { try await Task.sleep(for: .milliseconds(10)) }
        XCTAssertFalse(session.isRunning)
    }

    func testGoogleStopHoldsFliButSkiplaggedResumesNow() async throws {
        let store = try store()
        let c = try request.plan()
        // Fli blocked on day 1; Skiplagged goes offline on day 1 → both lanes leave items pending.
        let fli = ScriptedProvider("fli", pacing: ProviderPacing(interval: .milliseconds(250), maxInFlight: 1),
                                   [c[0].date: [.stop(.blocked("http_403"))]])
        let skip = ScriptedProvider("skiplagged", pacing: ProviderPacing(interval: .seconds(3), maxInFlight: 1),
                                    [c[0].date: [.stop(.offline)]])
        let stoppedAt = Date()
        let first = SearchSession(engine: SearchEngine(providers: [fli, skip], sleep: FakeClock().sleep), store: store, now: { stoppedAt })
        first.start(request, combos: c)
        try await waitUntilStopped(first)
        XCTAssertEqual(first.phase, .stopped(.offline))

        // 5 minutes later: Skiplagged items may resume, Fli items wait for the Google cooldown.
        let fli2 = ScriptedProvider("fli", pacing: ProviderPacing(interval: .milliseconds(250), maxInFlight: 1), [:])
        let skip2 = ScriptedProvider("skiplagged", pacing: ProviderPacing(interval: .seconds(3), maxInFlight: 1),
                                     [c[0].date: [ScriptedProvider.found("skiplagged", c[0], price: "3")],
                                      c[1].date: [ScriptedProvider.found("skiplagged", c[1], price: "4")]])
        let soon = SearchSession(engine: SearchEngine(providers: [fli2, skip2], sleep: FakeClock().sleep), store: store,
                                 now: { stoppedAt.addingTimeInterval(5 * 60) })
        soon.restoreLatest()
        XCTAssertTrue(soon.canResume, "Skiplagged items are not under the Google cooldown")
        soon.resume()
        try await waitUntilStopped(soon)
        let fliCalls = await fli2.script.calls
        let skipCalls = await skip2.script.calls
        XCTAssertTrue(fliCalls.isEmpty, "Fli waits 30 minutes after its block")
        XCTAssertEqual(skipCalls.sorted(), c.map(\.date))
        XCTAssertNotNil(soon.resumable, "Fli items still pending")
        XCTAssertFalse(soon.canResume)
        XCTAssertNotNil(soon.resumeAllowedAfter)
    }
}
