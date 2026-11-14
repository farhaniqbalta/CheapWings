import CheapWingsCore
@testable import CheapWingsKit
import XCTest

/// Transport whose replies the test releases one by one (by URL), so reply order is controlled.
actor GateTransport: FliTransport {
    enum Outcome { case page(FetchedPage), error(Error) }
    private var outcomes: [URL: Outcome]
    private var waiters: [URL: CheckedContinuation<Void, Never>] = [:]
    private var released: Set<URL> = []
    private(set) var started: [URL] = []
    private(set) var startTimes: [ContinuousClock.Instant] = []
    private(set) var inFlight = 0
    private(set) var maxSeenInFlight = 0
    private(set) var cancelledWaits = 0

    init(_ outcomes: [URL: Outcome], releaseAll: Bool = false) {
        self.outcomes = outcomes
        if releaseAll { released = Set(outcomes.keys) }
    }

    func fetch(_ url: URL) async throws -> FetchedPage {
        started.append(url)
        startTimes.append(.now)
        inFlight += 1
        maxSeenInFlight = max(maxSeenInFlight, inFlight)
        defer { inFlight -= 1 }
        if !released.contains(url) {
            await withTaskCancellationHandler {
                await withCheckedContinuation { waiters[url] = $0 }
            } onCancel: {
                Task { await self.wake(url) }
            }
        }
        if Task.isCancelled {
            cancelledWaits += 1
            throw CancellationError()
        }
        switch outcomes[url] {
        case .page(let page)?: return page
        case .error(let error)?: throw error
        case nil: throw URLError(.badURL)
        }
    }

    func release(_ url: URL) {
        released.insert(url)
        wake(url)
    }

    private func wake(_ url: URL) { waiters.removeValue(forKey: url)?.resume() }
}

/// A provider that is not Fli: proves the runner has no Fli knowledge.
struct SlowFakeProvider: SearchProvider {
    let id = "fake"
    let pacing = ProviderPacing(interval: .seconds(3), maxInFlight: 1)
    let counter = InFlightCounter()

    func search(_ combo: RouteDate, request: SearchRequest) async -> ProviderOutcome {
        await counter.enter()
        await counter.leave()
        let offer = FliOffer(price: "100", currency: "IDR", legs: [])
        return .found(offers: [FoundOffer(routeDate: combo, index: 0, offer: offer, searchURL: URL(string: "https://example.invalid")!)],
                      hidden: [])
    }
}

actor InFlightCounter {
    private(set) var now = 0
    private(set) var peak = 0
    func enter() { now += 1; peak = max(peak, now) }
    func leave() { now -= 1 }
}

final class ParallelPacingTests: XCTestCase {
    func request(days: Int) -> SearchRequest {
        let through = SearchModelDates.start.addingTimeInterval(Double(days - 1) * 86_400)
        return SearchRequest(origins: ["CGK"], destinations: ["DPS"], dateFrom: "2026-12-15",
                             dateThrough: SearchModelDates.ymd(through), currency: "IDR")
    }

    /// Page outcomes keyed by URL; `special` overrides by combo index (0-based).
    func outcomes(_ request: SearchRequest, _ combos: [RouteDate], special: [Int: GateTransport.Outcome] = [:]) -> [URL: GateTransport.Outcome] {
        Dictionary(uniqueKeysWithValues: combos.enumerated().map { i, combo in
            (request.searchURL(combo), special[i] ?? .page(page("CGK", "DPS", combo.date, prices: ["\(1_000_000 + i)"])))
        })
    }

    func consume(_ engine: SearchEngine, _ request: SearchRequest, _ combos: [RouteDate]) -> Task<[SearchEvent], Never> {
        Task {
            var events: [SearchEvent] = []
            for await event in engine.run(request, combos: combos) { events.append(event) }
            return events
        }
    }

    func waitStarted(_ transport: GateTransport, _ count: Int) async throws {
        for _ in 0..<300 {
            if await transport.started.count >= count { return }
            try await Task.sleep(for: .milliseconds(5))
        }
        XCTFail("only \(await transport.started.count) of \(count) started")
    }

    func progress(_ events: [SearchEvent]) -> [Int] {
        events.compactMap { if case .progress(let done, _) = $0 { return done } else { return nil } }
    }

    func offerDates(_ events: [SearchEvent]) -> [String] {
        events.flatMap { if case .offers(let o) = $0 { return o.map(\.routeDate.date) } else { return [] } }
    }

    func stopReason(_ events: [SearchEvent]) -> StopReason? {
        events.compactMap { if case .stopped(let r) = $0 { return r } else { return nil } }.last
    }

    func testStartsUpToMaxInFlightBeforeAnyReply() async throws {
        let request = request(days: 8), combos = try request.plan()
        let transport = GateTransport(outcomes(request, combos))
        let clock = FakeClock()
        let consumer = consume(SearchEngine(transport: transport, maxInFlight: 3, sleep: clock.sleep), request, combos)
        try await waitStarted(transport, 3)
        try await Task.sleep(for: .milliseconds(50))
        let started = await transport.started
        let peak = await transport.maxSeenInFlight
        // The first three route/dates (arrival order at the transport is not fixed: they start together).
        XCTAssertEqual(Set(started), Set(combos.prefix(3).map { request.searchURL($0) }))
        XCTAssertEqual(peak, 3)
        XCTAssertEqual(clock.sleeps, [.milliseconds(250), .milliseconds(250)])
        consumer.cancel()
        _ = await consumer.value
    }

    func testRepliesReleasedInPlanOrder() async throws {
        let request = request(days: 4), combos = try request.plan()
        let transport = GateTransport(outcomes(request, combos))
        let consumer = consume(SearchEngine(transport: transport, maxInFlight: 4, sleep: FakeClock().sleep), request, combos)
        try await waitStarted(transport, 4)
        for i in [3, 2, 1, 0] {
            await transport.release(request.searchURL(combos[i]))
            try await Task.sleep(for: .milliseconds(10))
        }
        let events = await consumer.value
        XCTAssertEqual(progress(events), [1, 2, 3, 4])
        XCTAssertEqual(offerDates(events), combos.map(\.date))
        XCTAssertEqual(stopReason(events), .finished)
    }

    func testSlotFreesOnlyWhenReleasedInOrder() async throws {
        let request = request(days: 3), combos = try request.plan()
        let transport = GateTransport(outcomes(request, combos))
        let consumer = consume(SearchEngine(transport: transport, maxInFlight: 2, sleep: FakeClock().sleep), request, combos)
        try await waitStarted(transport, 2)
        await transport.release(request.searchURL(combos[1]))
        try await Task.sleep(for: .milliseconds(50))
        let stillTwo = await transport.started.count
        XCTAssertEqual(stillTwo, 2, "reply 2 arrived but 1 is open: no new start")
        await transport.release(request.searchURL(combos[0]))
        try await waitStarted(transport, 3)
        await transport.release(request.searchURL(combos[2]))
        let events = await consumer.value
        XCTAssertEqual(progress(events), [1, 2, 3])
    }

    func testRateLimitMidFlightStopsAndDiscardsLater() async throws {
        let request = request(days: 6), combos = try request.plan()
        let limited = FetchedPage(status: 429, body: Data(), refusedRedirect: nil)
        let transport = GateTransport(outcomes(request, combos, special: [1: .page(limited)]))
        let consumer = consume(SearchEngine(transport: transport, maxInFlight: 4, sleep: FakeClock().sleep), request, combos)
        try await waitStarted(transport, 4)
        for i in [2, 3, 1, 0] {
            await transport.release(request.searchURL(combos[i]))
            try await Task.sleep(for: .milliseconds(10))
        }
        let events = await consumer.value
        XCTAssertEqual(offerDates(events), [combos[0].date], "later replies are discarded, not saved")
        XCTAssertEqual(progress(events), [1])
        XCTAssertEqual(stopReason(events), .rateLimited)
        let started = await transport.started.count
        XCTAssertEqual(started, 4, "no new request after the 429")
    }

    func testOfflineMidFlightOneStopNoFailures() async throws {
        let request = request(days: 4), combos = try request.plan()
        let offline = GateTransport.Outcome.error(URLError(.notConnectedToInternet))
        let transport = GateTransport(outcomes(request, combos, special: [1: offline, 2: offline, 3: offline]))
        let consumer = consume(SearchEngine(transport: transport, maxInFlight: 4, sleep: FakeClock().sleep), request, combos)
        try await waitStarted(transport, 4)
        for i in [3, 2, 1, 0] { await transport.release(request.searchURL(combos[i])) }
        let events = await consumer.value
        XCTAssertEqual(stopReason(events), .offline)
        XCTAssertFalse(events.contains { if case .comboFailed = $0 { return true } else { return false } })
        XCTAssertEqual(events.filter { if case .stopped = $0 { return true } else { return false } }.count, 1)
    }

    func testNetworkErrorStillContinuesInOrder() async throws {
        let request = request(days: 3), combos = try request.plan()
        let transport = GateTransport(outcomes(request, combos, special: [1: .error(URLError(.timedOut))]), releaseAll: true)
        let events = await consume(SearchEngine(transport: transport, maxInFlight: 3, sleep: FakeClock().sleep), request, combos).value
        let failed = events.compactMap { if case .comboFailed(let c, let code) = $0 { return "\(c.date) \(code)" } else { return nil } }
        XCTAssertEqual(failed, ["\(combos[1].date) network"])
        XCTAssertEqual(progress(events), [1, 2, 3])
        XCTAssertEqual(stopReason(events), .finished)
    }

    func testCancelCancelsAllInFlight() async throws {
        let request = request(days: 6), combos = try request.plan()
        let transport = GateTransport(outcomes(request, combos))
        let consumer = consume(SearchEngine(transport: transport, maxInFlight: 4, sleep: FakeClock().sleep), request, combos)
        try await waitStarted(transport, 4)
        consumer.cancel()
        let events = await consumer.value
        try await Task.sleep(for: .milliseconds(50))
        let cancelled = await transport.cancelledWaits
        let started = await transport.started.count
        XCTAssertEqual(cancelled, 4)
        XCTAssertEqual(started, 4)
        XCTAssertTrue(offerDates(events).isEmpty)
    }

    func testMinimumStartGap() async throws {
        let request = request(days: 5), combos = try request.plan()
        let transport = GateTransport(outcomes(request, combos), releaseAll: true)
        let engine = SearchEngine(transport: transport, interval: .milliseconds(20), maxInFlight: 5)
        _ = await consume(engine, request, combos).value
        let times = await transport.startTimes
        XCTAssertEqual(times.count, 5)
        for (a, b) in zip(times, times.dropFirst()) {
            XCTAssertGreaterThanOrEqual(b - a, .milliseconds(20))
        }
    }

    func testRunnerHonoursProviderPacing() async throws {
        let request = request(days: 3), combos = try request.plan()
        let provider = SlowFakeProvider()
        let clock = FakeClock()
        let events = await consume(SearchEngine(provider: provider, sleep: clock.sleep), request, combos).value
        let peak = await provider.counter.peak
        XCTAssertEqual(clock.sleeps, [.seconds(3), .seconds(3)])
        XCTAssertEqual(peak, 1)
        XCTAssertEqual(progress(events), [1, 2, 3])
        XCTAssertEqual(stopReason(events), .finished)
    }

    func testFliProviderMapsResponses() async throws {
        let request = request(days: 1), combo = try request.plan()[0]
        func outcome(_ result: Result<FetchedPage, Error>) async -> ProviderOutcome {
            await FliSearchProvider(transport: FakeTransport(results: [result])).search(combo, request: request)
        }
        if case .found(let offers, _) = await outcome(.success(page("CGK", "DPS", combo.date, prices: ["1250000"]))) {
            XCTAssertEqual(offers.map(\.offer.price), ["1250000"])
        } else { XCTFail("200 page") }
        guard case .stop(.rateLimited) = await outcome(.success(FetchedPage(status: 429, body: Data(), refusedRedirect: nil))) else { return XCTFail("429") }
        guard case .stop(.blocked("http_403")) = await outcome(.success(FetchedPage(status: 403, body: Data(), refusedRedirect: nil))) else { return XCTFail("403") }
        guard case .stop(.offline) = await outcome(.failure(URLError(.cannotFindHost))) else { return XCTFail("dns") }
        guard case .failed("network", _) = await outcome(.failure(URLError(.timedOut))) else { return XCTFail("timeout") }
        guard case .failed("schema_changed", _) = await outcome(.success(brokenPage)) else { return XCTFail("broken") }
        XCTAssertEqual(FliSearchProvider(transport: FakeTransport([])).id, "fli")
        XCTAssertEqual(ProviderPacing.fli.maxInFlight, 6)
        XCTAssertEqual(ProviderPacing.fli.interval, .milliseconds(250))
    }
}

/// Test-only date helpers (the app's SearchModel helpers are not in the Kit).
enum SearchModelDates {
    static let start: Date = {
        var c = Calendar(identifier: .gregorian)
        c.timeZone = TimeZone(identifier: "UTC")!
        return c.date(from: DateComponents(year: 2026, month: 12, day: 15))!
    }()

    static func ymd(_ date: Date) -> String {
        var c = Calendar(identifier: .gregorian)
        c.timeZone = TimeZone(identifier: "UTC")!
        let d = c.dateComponents([.year, .month, .day], from: date)
        return String(format: "%04d-%02d-%02d", d.year!, d.month!, d.day!)
    }
}
