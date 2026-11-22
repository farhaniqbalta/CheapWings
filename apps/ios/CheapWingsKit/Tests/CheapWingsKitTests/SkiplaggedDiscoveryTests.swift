import CheapWingsCore
@testable import CheapWingsKit
import XCTest

/// The recorded SUB 2026-12-22 anywhere reply (P7.1 probe) from the shared discovery fixture.
let recordedAnywhereReply: String = {
    var url = URL(fileURLWithPath: #filePath)
    for _ in 0..<6 { url.deleteLastPathComponent() }
    let data = try! Data(contentsOf: url.appendingPathComponent("contracts/fixtures/core/discovery_sources_fixtures.json"))
    let cases = (try! JSONSerialization.jsonObject(with: data) as! [String: Any])["anywhere"] as! [[String: Any]]
    return cases.first { $0["name"] as? String == "probe_SUB_2026-12-22" }!["rpc_json"] as! String
}()

final class SkiplaggedDiscoveryTests: XCTestCase {
    let call = DiscoveryCall(origin: "SUB", date: "2026-12-22")
    let fetchedAt = Date(timeIntervalSince1970: 1_800_000_000)

    func discover(_ replies: [Result<MCPReply, Error>]) async -> DiscoveryOutcome {
        await SkiplaggedDiscoveryProvider(transport: FakeMCPTransport(replies)).discover(call, currency: "IDR", fetchedAt: fetchedAt)
    }

    func testArgumentsMatchTheProbe() async throws {
        let transport = FakeMCPTransport([initReply, initializedReply, reply(200, recordedAnywhereReply)])
        let provider = SkiplaggedDiscoveryProvider(transport: transport)
        _ = await provider.discover(call, currency: "IDR", fetchedAt: fetchedAt)
        let sent = await transport.sent
        XCTAssertEqual(sent.last?.params["name"] as? String, "sk_destinations_anywhere")
        let args = try XCTUnwrap(sent.last?.params["arguments"] as? [String: Any])
        XCTAssertEqual(args["from"] as? String, "SUB")
        XCTAssertEqual(args["depart"] as? String, "2026-12-22")
        XCTAssertEqual(args["currency"] as? String, "IDR")
        XCTAssertEqual(args["fare_class"] as? String, "economy")
        XCTAssertEqual(args["adults"] as? Int, 1)
        XCTAssertEqual(provider.id, "skiplagged")
        XCTAssertEqual(provider.pacing, SkiplaggedSearchProvider().pacing)
    }

    func testRecordedReplyIsAPage() async {
        guard case .page(let page) = await discover([initReply, initializedReply, reply(200, recordedAnywhereReply)])
        else { return XCTFail("page") }
        XCTAssertEqual(page.observations.count, 42)
        XCTAssertEqual(page.observations[0].destination, "DPS")
        XCTAssertEqual(page.observations[0].amount, "46")
        XCTAssertEqual(page.observations[0].fetchedAt, "2027-01-15T08:00:00Z")
        XCTAssertEqual(page.fx.map(\.currency), ["USD"])
        XCTAssertEqual(page.unpriced, 0)
    }

    func testRateLimitRetriesAfterHeader() async {
        guard case .retry(let after) = await discover([initReply, initializedReply, reply(429, "", headers: ["retry-after": "5"])])
        else { return XCTFail("retry") }
        XCTAssertEqual(after, .seconds(5))
    }

    func testForbiddenStopsTheSource() async {
        guard case .stop(.blocked("http_403")) = await discover([initReply, initializedReply, reply(403)]) else { return XCTFail("403") }
    }

    func testOfflineStops() async {
        guard case .stop(.offline) = await discover([.failure(URLError(.notConnectedToInternet))]) else { return XCTFail("offline") }
    }

    func testMalformedReplyIsSchemaChanged() async {
        let bad = #"{"jsonrpc":"2.0","id":2,"result":{"content":[{"type":"text","text":"nope"}],"structuredContent":{"pricing":{}}}}"#
        guard case .failed("schema_changed") = await discover([initReply, initializedReply, reply(200, bad)]) else { return XCTFail("schema") }
    }
}
