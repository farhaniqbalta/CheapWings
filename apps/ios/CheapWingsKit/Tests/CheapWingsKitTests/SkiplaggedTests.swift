import CheapWingsCore
@testable import CheapWingsKit
import XCTest

/// Scripted MCP server: returns queued replies in order and records each request.
actor FakeMCPTransport: MCPTransport {
    struct Sent { let method: String; let id: Int?; let headers: [String: String]; let params: [String: Any] }
    private var replies: [Result<MCPReply, Error>]
    private(set) var sent: [Sent] = []

    init(_ replies: [Result<MCPReply, Error>]) { self.replies = replies }

    func post(_ body: Data, headers: [String: String]) async throws -> MCPReply {
        let json = (try? JSONSerialization.jsonObject(with: body)) as? [String: Any] ?? [:]
        sent.append(Sent(method: json["method"] as? String ?? "?", id: json["id"] as? Int, headers: headers,
                         params: json["params"] as? [String: Any] ?? [:]))
        return try replies.removeFirst().get()
    }
}

func reply(_ status: Int = 200, _ body: String = "", headers: [String: String] = ["content-type": "application/json"]) -> Result<MCPReply, Error> {
    .success(MCPReply(status: status, headers: headers, body: Data(body.utf8)))
}

let initReply = reply(200, #"{"jsonrpc":"2.0","id":1,"result":{"protocolVersion":"2025-11-25","capabilities":{}}}"#,
                      headers: ["content-type": "application/json", "mcp-session-id": "s1"])
let initializedReply = reply(202)

/// The recorded MEL→DPS payload (exact numbers) wrapped as a JSON-RPC tools/call result.
let recordedPayload: String = {
    var url = URL(fileURLWithPath: #filePath)
    for _ in 0..<6 { url.deleteLastPathComponent() }
    let data = try! Data(contentsOf: url.appendingPathComponent("contracts/fixtures/core/core_fixtures.json"))
    let cases = (try! JSONSerialization.jsonObject(with: data) as! [String: Any])["skiplagged"] as! [[String: Any]]
    return cases.first { $0["name"] as? String == "recorded_idr" }!["json"] as! String
}()

func toolReply(id: Int = 2, payload: String = recordedPayload) -> String {
    #"{"jsonrpc":"2.0","id":\#(id),"result":{"content":[{"type":"text","text":"summary"}],"structuredContent":\#(payload),"isError":false}}"#
}

final class MCPClientTests: XCTestCase {
    func testHandshakeThenToolCall() async throws {
        let transport = FakeMCPTransport([initReply, initializedReply, reply(200, toolReply())])
        let raw = try await MCPClient(transport: transport).callTool(name: "sk_flights_search", arguments: ["origin": "MEL"])
        XCTAssertEqual(raw, toolReply())
        let sent = await transport.sent
        XCTAssertEqual(sent.map(\.method), ["initialize", "notifications/initialized", "tools/call"])
        XCTAssertNil(sent[0].headers["Mcp-Session-Id"])
        XCTAssertEqual(sent[1].headers["Mcp-Session-Id"], "s1")
        XCTAssertEqual(sent[2].headers["Mcp-Session-Id"], "s1")
        XCTAssertEqual(sent[2].headers["MCP-Protocol-Version"], "2025-11-25")
        XCTAssertEqual(sent[0].params["protocolVersion"] as? String, "2025-11-25")
        XCTAssertNil(sent[1].id, "initialized is a notification")
        XCTAssertEqual(sent[2].params["name"] as? String, "sk_flights_search")
    }

    func testSSEReplyParsed() async throws {
        let sse = "event: message\nid: e1\ndata: \(toolReply())\n\n"
        let transport = FakeMCPTransport([initReply, initializedReply,
                                          reply(200, sse, headers: ["content-type": "text/event-stream"])])
        let raw = try await MCPClient(transport: transport).callTool(name: "sk_flights_search", arguments: [:])
        XCTAssertEqual(raw, toolReply())
    }

    func testSessionReusedAcrossCalls() async throws {
        let transport = FakeMCPTransport([initReply, initializedReply, reply(200, toolReply()), reply(200, toolReply(id: 3))])
        let client = MCPClient(transport: transport)
        _ = try await client.callTool(name: "sk_flights_search", arguments: [:])
        _ = try await client.callTool(name: "sk_flights_search", arguments: [:])
        let methods = await transport.sent.map(\.method)
        XCTAssertEqual(methods, ["initialize", "notifications/initialized", "tools/call", "tools/call"])
    }

    func testExpiredSessionReinitializesOnce() async throws {
        let transport = FakeMCPTransport([initReply, initializedReply, reply(404),
                                          initReply, initializedReply, reply(200, toolReply(id: 4))])
        let raw = try await MCPClient(transport: transport).callTool(name: "sk_flights_search", arguments: [:])
        XCTAssertTrue(raw.contains("structuredContent"))
        let methods = await transport.sent.map(\.method)
        XCTAssertEqual(methods, ["initialize", "notifications/initialized", "tools/call",
                                 "initialize", "notifications/initialized", "tools/call"])
    }

    func testHTTPErrorCarriesRetryAfter() async throws {
        let transport = FakeMCPTransport([initReply, initializedReply,
                                          reply(429, "", headers: ["retry-after": "30"])])
        do {
            _ = try await MCPClient(transport: transport).callTool(name: "sk_flights_search", arguments: [:])
            XCTFail("expected an HTTP error")
        } catch MCPError.http(let status, let retryAfter) {
            XCTAssertEqual(status, 429)
            XCTAssertEqual(retryAfter, "30")
        }
    }
}

/// Replies by method (order-independent, for concurrent calls); tools/call replies echo the id.
actor RoutingMCPTransport: MCPTransport {
    private(set) var methods: [String] = []
    private(set) var versionHeaders: [String?] = []
    private var toolStatuses: [Int]
    private let serverVersion: String
    private var session = 0

    init(toolStatuses: [Int] = [], serverVersion: String = "2025-11-25") {
        self.toolStatuses = toolStatuses
        self.serverVersion = serverVersion
    }

    func post(_ body: Data, headers: [String: String]) async throws -> MCPReply {
        let json = (try? JSONSerialization.jsonObject(with: body)) as? [String: Any] ?? [:]
        let method = json["method"] as? String ?? "?"
        methods.append(method)
        versionHeaders.append(headers["MCP-Protocol-Version"])
        await Task.yield()  // let another caller interleave, like a slow network
        switch method {
        case "initialize":
            session += 1
            let body = #"{"jsonrpc":"2.0","id":\#(json["id"] as? Int ?? 0),"result":{"protocolVersion":"\#(serverVersion)","capabilities":{}}}"#
            return MCPReply(status: 200, headers: ["content-type": "application/json", "mcp-session-id": "s\(session)"], body: Data(body.utf8))
        case "notifications/initialized":
            return MCPReply(status: 202, headers: [:], body: Data())
        default:
            let status = toolStatuses.isEmpty ? 200 : toolStatuses.removeFirst()
            guard status == 200 else { return MCPReply(status: status, headers: [:], body: Data()) }
            return MCPReply(status: 200, headers: ["content-type": "application/json"], body: Data(toolReply(id: json["id"] as? Int ?? 0).utf8))
        }
    }
}

final class MCPConcurrencyTests: XCTestCase {
    func testConcurrentCallsShareOneHandshake() async throws {
        let transport = RoutingMCPTransport()
        let client = MCPClient(transport: transport)
        async let a = client.callTool(name: "sk_flights_search", arguments: [:])
        async let b = client.callTool(name: "sk_flights_search", arguments: [:])
        async let c = client.callTool(name: "sk_flights_search", arguments: [:])
        _ = try await (a, b, c)
        let methods = await transport.methods
        XCTAssertEqual(methods.filter { $0 == "initialize" }.count, 1, "\(methods)")
        XCTAssertEqual(methods.filter { $0 == "tools/call" }.count, 3)
    }

    func testExpiredSessionReinitializesOnceForConcurrentCalls() async throws {
        let transport = RoutingMCPTransport(toolStatuses: [200, 404, 404])
        let client = MCPClient(transport: transport)
        _ = try await client.callTool(name: "sk_flights_search", arguments: [:])
        async let b = client.callTool(name: "sk_flights_search", arguments: [:])
        async let c = client.callTool(name: "sk_flights_search", arguments: [:])
        _ = try await (b, c)
        let methods = await transport.methods
        XCTAssertEqual(methods.filter { $0 == "initialize" }.count, 2, "one first handshake, one re-handshake: \(methods)")
    }

    func testNegotiatedVersionIsSent() async throws {
        let transport = RoutingMCPTransport(serverVersion: "2025-06-18")
        _ = try await MCPClient(transport: transport).callTool(name: "sk_flights_search", arguments: [:])
        let headers = await transport.versionHeaders
        XCTAssertEqual(headers.last ?? nil, "2025-06-18", "later requests carry the version the server agreed")
    }
}

final class SkiplaggedProviderTests: XCTestCase {
    let request = SearchRequest(origins: ["MEL"], destinations: ["DPS"], dateFrom: "2026-12-16",
                                dateThrough: "2026-12-16", currency: "IDR")
    var combo: RouteDate { try! request.plan()[0] }

    func fetch(_ replies: [Result<MCPReply, Error>]) async -> SkiplaggedFetch {
        await SkiplaggedSearchProvider(transport: FakeMCPTransport(replies)).fetch(combo, request: request)
    }

    func testArgumentsMatchTheWeb() async throws {
        let transport = FakeMCPTransport([initReply, initializedReply, reply(200, toolReply())])
        _ = await SkiplaggedSearchProvider(transport: transport).fetch(combo, request: request)
        let sent = await transport.sent
        let args = try XCTUnwrap(sent.last?.params["arguments"] as? [String: Any])
        XCTAssertEqual(args["origin"] as? String, "MEL")
        XCTAssertEqual(args["destination"] as? String, "DPS")
        XCTAssertEqual(args["departureDate"] as? String, "2026-12-16")
        XCTAssertEqual(args["adults"] as? Int, 1)
        XCTAssertEqual(args["fareClass"] as? String, "economy")
        XCTAssertEqual(args["limit"] as? Int, 20)
        XCTAssertEqual(args["includeHiddenCity"] as? Bool, false)
        XCTAssertEqual(args["includeVirtualInterlining"] as? Bool, false)
        XCTAssertEqual(args["currency"] as? String, "IDR")
        XCTAssertEqual(SkiplaggedSearchProvider(transport: transport).pacing, ProviderPacing(interval: .seconds(3), maxInFlight: 3))
    }

    func testFetchParsesExactPage() async throws {
        guard case .page(let page) = await fetch([initReply, initializedReply, reply(200, toolReply())]) else { return XCTFail("page") }
        XCTAssertEqual(page.offers.count, 5)
        XCTAssertEqual(page.offers[0].priceOriginal, "271")
        XCTAssertEqual(page.offers[0].priceComparable, "4907458")
        XCTAssertEqual(page.offers[0].fx?.rate, "18108.7")
        XCTAssertEqual(page.complete, false)
    }

    func testRateLimitedRetriesAfterHeader() async {
        guard case .outcome(.retry(let after)) = await fetch([initReply, initializedReply, reply(429, "", headers: ["retry-after": "30"])])
        else { return XCTFail("seconds") }
        XCTAssertEqual(after, .seconds(30))
        guard case .outcome(.retry(let fallback)) = await fetch([initReply, initializedReply, reply(429)]) else { return XCTFail("default") }
        XCTAssertEqual(fallback, .seconds(60))
        let soon = Date().addingTimeInterval(120)
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "en_US_POSIX")
        formatter.timeZone = TimeZone(identifier: "GMT")
        formatter.dateFormat = "EEE, dd MMM yyyy HH:mm:ss 'GMT'"
        guard case .outcome(.retry(let dated)) = await fetch([initReply, initializedReply,
                                                              reply(429, "", headers: ["retry-after": formatter.string(from: soon)])])
        else { return XCTFail("date") }
        XCTAssertGreaterThan(dated, .seconds(110))
        XCTAssertLessThanOrEqual(dated, .seconds(121))
    }

    func testForbiddenStopsTheLane() async {
        guard case .outcome(.stop(.blocked("http_403"))) = await fetch([initReply, initializedReply, reply(403)]) else { return XCTFail("403") }
    }

    func testToolErrorIsProviderUnavailable() async {
        let error = #"{"jsonrpc":"2.0","id":2,"result":{"content":[],"isError":true}}"#
        guard case .outcome(.failed("provider_unavailable", _)) = await fetch([initReply, initializedReply, reply(200, error)])
        else { return XCTFail("tool error") }
    }

    func testOfflineStopsAndTimeoutFails() async {
        guard case .outcome(.stop(.offline)) = await fetch([.failure(URLError(.notConnectedToInternet))]) else { return XCTFail("offline") }
        guard case .outcome(.failed("network", _)) = await fetch([.failure(URLError(.timedOut))]) else { return XCTFail("timeout") }
    }

    func testWrongRouteIsSchemaChanged() async {
        let other = SearchRequest(origins: ["SYD"], destinations: ["DPS"], dateFrom: "2026-12-16",
                                  dateThrough: "2026-12-16", currency: "IDR")
        let result = await SkiplaggedSearchProvider(transport: FakeMCPTransport([initReply, initializedReply, reply(200, toolReply())]))
            .fetch(try! other.plan()[0], request: other)
        guard case .outcome(.failed("schema_changed", _)) = result else { return XCTFail("schema") }
    }
}
