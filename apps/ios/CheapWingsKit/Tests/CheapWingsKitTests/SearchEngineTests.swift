import CheapWingsCore
@testable import CheapWingsKit
import XCTest

/// Scripted transport: returns queued pages in order and records every fetch.
actor FakeTransport: FliTransport {
    private var queue: [Result<FetchedPage, Error>]
    private(set) var fetched: [URL] = []
    private(set) var cancelledFetches = 0
    private let hang: Bool
    private var hangFirst: Int
    private let hangWhenEmpty: Bool

    /// By default an extra fetch past the scripted pages crashes the test (catches surprise
    /// requests); `hangWhenEmpty` instead simulates a request still in flight.
    init(_ pages: [FetchedPage], hangOnFetch: Bool = false, hangFirst: Int = 0, hangWhenEmpty: Bool = false) {
        queue = pages.map { .success($0) }
        hang = hangOnFetch
        self.hangFirst = hangFirst
        self.hangWhenEmpty = hangWhenEmpty
    }

    init(results: [Result<FetchedPage, Error>]) {
        queue = results
        hang = false
        hangFirst = 0
        hangWhenEmpty = false
    }

    func fetch(_ url: URL) async throws -> FetchedPage {
        fetched.append(url)
        let hangThis = hang || hangFirst > 0 || (hangWhenEmpty && queue.isEmpty)
        hangFirst = max(0, hangFirst - 1)
        if hangThis {
            do { try await Task.sleep(for: .seconds(30)) } catch {  // until cancelled
                cancelledFetches += 1
                throw error
            }
        }
        return try queue.removeFirst().get()
    }
}

/// Records requested sleeps instead of sleeping.
final class FakeClock: @unchecked Sendable {
    private let lock = NSLock()
    private var _sleeps: [Duration] = []
    var sleeps: [Duration] { lock.withLock { _sleeps } }
    var sleep: @Sendable (Duration) async throws -> Void {
        { [self] d in lock.withLock { _sleeps.append(d) } }
    }
}

/// A one-row ds:1 page per priced flight, in the layout the Rust decoder reads.
func page(_ origin: String, _ destination: String, _ date: String, prices: [String], currencyToken: String = "GgUaA0lEUg") -> FetchedPage {
    let ymd = date.split(separator: "-").map { String(Int($0)!) }.joined(separator: ",")
    let rows = prices.enumerated().map { i, price in
        var leg = Array(repeating: "null", count: 23)
        leg[3] = "\"\(origin)\""; leg[6] = "\"\(destination)\""
        leg[8] = "[6,5]"; leg[10] = "[9,0]"; leg[11] = "115"
        leg[20] = "[\(ymd)]"; leg[21] = "[\(ymd)]"
        leg[22] = "[\"GA\",\"\(400 + i)\",null]"
        let detail = "[null,null,[[\(leg.joined(separator: ","))]],null,null,null,null,null,null,115]"
        return "[\(detail),[[null,\(price)],\"\(currencyToken)\"]]"
    }.joined(separator: ",")
    let html = "<script>AF_initDataCallback({key: 'ds:1', hash: '2', data:[null,null,[[\(rows)]],null], sideChannel: {}});</script>"
    return FetchedPage(status: 200, body: Data(html.utf8), refusedRedirect: nil)
}

let brokenPage = FetchedPage(status: 200, body: Data("<html>no data</html>".utf8), refusedRedirect: nil)
let trafficPage = FetchedPage(status: 200, body: Data("Our systems have detected unusual traffic".utf8), refusedRedirect: nil)
let rateLimited = FetchedPage(status: 429, body: Data(), refusedRedirect: nil)

final class SearchEngineTests: XCTestCase {
    let request = SearchRequest(origins: ["CGK"], destinations: ["DPS"], dateFrom: "2026-12-15",
                                dateThrough: "2026-12-17", currency: "IDR")

    func combos() throws -> [RouteDate] { try request.plan() }

    func collect(_ engine: SearchEngine, _ combos: [RouteDate]) async -> [SearchEvent] {
        var events: [SearchEvent] = []
        for await event in await engine.run(request, combos: combos) { events.append(event) }
        return events
    }

    func offers(_ events: [SearchEvent]) -> [FoundOffer] {
        events.flatMap { if case .offers(let o) = $0 { return o } else { return [] } }
    }

    func failures(_ events: [SearchEvent]) -> [String] {
        events.compactMap { if case .comboFailed(_, let code) = $0 { return code } else { return nil } }
    }

    func stop(_ events: [SearchEvent]) -> StopReason? {
        events.compactMap { if case .stopped(let r) = $0 { return r } else { return nil } }.last
    }

    func testRequestsArePacedAtInterval() async throws {
        let transport = FakeTransport([page("CGK", "DPS", "2026-12-15", prices: ["1250000"]),
                                       page("CGK", "DPS", "2026-12-16", prices: ["1300000"]),
                                       page("CGK", "DPS", "2026-12-17", prices: ["1100000"])])
        let clock = FakeClock()
        let events = await collect(SearchEngine(transport: transport, sleep: clock.sleep), try combos())
        // 0.25 s owner-approved after the 270-request live test (docs/log/p5.5-fli-interval.md).
        XCTAssertEqual(clock.sleeps, [.milliseconds(250), .milliseconds(250)])
        let fetched = await transport.fetched
        XCTAssertEqual(fetched.map { $0.absoluteString }, try combos().map {
            fliSearchUrl(origin: $0.origin, destination: $0.destination, date: $0.date, currency: "IDR", country: "ID")
        })
        XCTAssertEqual(offers(events).count, 3)
        XCTAssertEqual(stop(events), .finished)
    }

    func testStopsOn429AndKeepsEarlierOffers() async throws {
        let transport = FakeTransport([page("CGK", "DPS", "2026-12-15", prices: ["1250000"]), rateLimited])
        let events = await collect(SearchEngine(transport: transport, sleep: FakeClock().sleep), try combos())
        XCTAssertEqual(offers(events).count, 1)
        XCTAssertEqual(stop(events), .rateLimited)
        let count = await transport.fetched.count
        XCTAssertEqual(count, 2)
    }

    func testStopsOnRefusedRedirect() async throws {
        let sorry = FetchedPage(status: 302, body: Data(), refusedRedirect: URL(string: "https://www.google.com/sorry/index?continue=x")!)
        let transport = FakeTransport([sorry])
        let events = await collect(SearchEngine(transport: transport, sleep: FakeClock().sleep), try combos())
        XCTAssertEqual(stop(events), .blocked("www.google.com/sorry/index"))
        let count = await transport.fetched.count
        XCTAssertEqual(count, 1)
    }

    func testStopsOnAuthDenied() async throws {
        let transport = FakeTransport([trafficPage])
        let events = await collect(SearchEngine(transport: transport, sleep: FakeClock().sleep), try combos())
        XCTAssertEqual(stop(events), .blocked("auth_denied"))
        let count = await transport.fetched.count
        XCTAssertEqual(count, 1)
    }

    func testStopsOn403LikeProvidersFliDeny() async throws {
        let forbidden = FetchedPage(status: 403, body: Data(), refusedRedirect: nil)
        let transport = FakeTransport([page("CGK", "DPS", "2026-12-15", prices: ["1250000"]), forbidden])
        let events = await collect(SearchEngine(transport: transport, sleep: FakeClock().sleep), try combos())
        XCTAssertEqual(offers(events).count, 1)
        XCTAssertEqual(stop(events), .blocked("http_403"))
        let count = await transport.fetched.count
        XCTAssertEqual(count, 2)
    }

    func testOfflineErrorStopsAndLeavesComboPending() async throws {
        let transport = FakeTransport(results: [.success(page("CGK", "DPS", "2026-12-15", prices: ["1250000"])),
                                                .failure(URLError(.notConnectedToInternet))])
        let events = await collect(SearchEngine(transport: transport, sleep: FakeClock().sleep), try combos())
        XCTAssertEqual(stop(events), .offline)
        XCTAssertEqual(offers(events).count, 1)
        XCTAssertTrue(failures(events).isEmpty, "offline is a pause, not a failed route/date")
        let progress = events.filter { if case .progress = $0 { return true } else { return false } }
        XCTAssertEqual(progress.count, 1)
    }

    func testNoInternetBehindWiFiPausesToo() async throws {
        // Wi-Fi up but no internet (captive portal, dead router): DNS / host errors, not "offline".
        for code in [URLError.Code.cannotFindHost, .dnsLookupFailed, .cannotConnectToHost] {
            let transport = FakeTransport(results: Array(repeating: .failure(URLError(code)), count: 3))
            let events = await collect(SearchEngine(transport: transport, sleep: FakeClock().sleep), try combos())
            XCTAssertEqual(stop(events), .offline, "\(code)")
            XCTAssertTrue(failures(events).isEmpty, "\(code)")
        }
    }

    func testTimeoutStillFailsOnlyThatCombo() async throws {
        let transport = FakeTransport(results: [.failure(URLError(.timedOut)),
                                                .success(page("CGK", "DPS", "2026-12-16", prices: ["1300000"])),
                                                .success(page("CGK", "DPS", "2026-12-17", prices: ["1100000"]))])
        let events = await collect(SearchEngine(transport: transport, sleep: FakeClock().sleep), try combos())
        XCTAssertEqual(failures(events), ["network"])
        XCTAssertEqual(offers(events).count, 2)
        XCTAssertEqual(stop(events), .finished)
    }

    func testSchemaChangedContinues() async throws {
        let transport = FakeTransport([brokenPage, page("CGK", "DPS", "2026-12-16", prices: ["1300000"]), brokenPage])
        let events = await collect(SearchEngine(transport: transport, sleep: FakeClock().sleep), try combos())
        XCTAssertEqual(failures(events), ["schema_changed", "schema_changed"])
        XCTAssertEqual(offers(events).count, 1)
        XCTAssertEqual(stop(events), .finished)
    }

    func testAllFailedIsDistinguishable() async throws {
        let transport = FakeTransport([brokenPage, brokenPage, brokenPage])
        let events = await collect(SearchEngine(transport: transport, sleep: FakeClock().sleep), try combos())
        XCTAssertTrue(offers(events).isEmpty)
        XCTAssertEqual(failures(events).count, 3)
        XCTAssertEqual(stop(events), .finished)
    }

    func testCancellationStopsFurtherRequests() async throws {
        let transport = FakeTransport([page("CGK", "DPS", "2026-12-15", prices: ["1"])], hangOnFetch: true)
        let engine = SearchEngine(transport: transport, sleep: FakeClock().sleep)
        let combos = try combos()
        let consumer = Task { () -> [SearchEvent] in
            var events: [SearchEvent] = []
            for await event in await engine.run(request, combos: combos) { events.append(event) }
            return events
        }
        try await Task.sleep(for: .milliseconds(100))
        consumer.cancel()
        let events = await consumer.value
        try await Task.sleep(for: .milliseconds(100))
        let count = await transport.fetched.count
        let cancelled = await transport.cancelledFetches
        XCTAssertEqual(count, 1)
        XCTAssertEqual(cancelled, 1, "cancelling the consumer must cancel the in-flight request")
        XCTAssertTrue(offers(events).isEmpty)
    }

    func testCrossCheckMismatchIsDropped() async throws {
        let transport = FakeTransport([page("CGK", "SUB", "2026-12-15", prices: ["1250000"]),
                                       page("CGK", "DPS", "2026-12-16", prices: ["1300000"]),
                                       page("CGK", "DPS", "2026-12-17", prices: ["1100000"])])
        let events = await collect(SearchEngine(transport: transport, sleep: FakeClock().sleep), try combos())
        XCTAssertEqual(failures(events), ["cross_check: airports CGK-SUB"])
        XCTAssertEqual(offers(events).count, 2)
    }

    func testOneCurrencylessRowDoesNotDiscardThePage() async throws {
        // Live CGK→HND pages mixed rows with and without a currency token (P5.2 owner test).
        let mixed = page("CGK", "DPS", "2026-12-15", prices: ["1250000", "4161210"])
        let html = String(decoding: mixed.body, as: UTF8.self)
        // Strip the token from the second row only.
        let second = html.range(of: "\"GgUaA0lEUg\"", options: .backwards)!
        let patched = html.replacingCharacters(in: second, with: "null")
        let transport = FakeTransport([FetchedPage(status: 200, body: Data(patched.utf8), refusedRedirect: nil)])
        let oneDay = try SearchRequest(origins: ["CGK"], destinations: ["DPS"], dateFrom: "2026-12-15",
                                       dateThrough: "2026-12-15", currency: "IDR").plan()
        let events = await collect(SearchEngine(transport: transport, sleep: FakeClock().sleep), oneDay)
        XCTAssertEqual(offers(events).map(\.offer.price), ["1250000"])
        XCTAssertTrue(failures(events).isEmpty)
        let hidden = events.compactMap { if case .offersHidden(_, let reasons) = $0 { return reasons } else { return nil } }
        XCTAssertEqual(hidden, [["currency None"]])
    }

    func testRankingIsAscendingByExactPrice() throws {
        let usd = "GgUaA1VTRA"
        let request = SearchRequest(origins: ["CGK"], destinations: ["DPS"], dateFrom: "2026-12-15",
                                    dateThrough: "2026-12-15", currency: "USD")
        let combo = try request.plan()[0]
        let decoded = try fliDecodePage(html: String(decoding: page("CGK", "DPS", "2026-12-15", prices: ["980.5", "75", "1234.50"], currencyToken: usd).body, as: UTF8.self))
        let found = decoded.offers.enumerated().map { i, offer in
            FoundOffer(routeDate: combo, index: i, offer: offer, searchURL: URL(string: "https://example.invalid")!)
        }
        XCTAssertEqual(rankLowestAdvertised(found).map(\.offer.price), ["75", "980.5", "1234.50"])
    }
}
