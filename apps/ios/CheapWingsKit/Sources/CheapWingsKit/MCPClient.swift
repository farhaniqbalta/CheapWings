import Foundation

/// One HTTP reply from an MCP server; header names lower-cased.
public struct MCPReply: Sendable {
    public let status: Int
    public let headers: [String: String]
    public let body: Data

    public init(status: Int, headers: [String: String], body: Data) {
        self.status = status
        self.headers = headers
        self.body = body
    }
}

/// POSTs one JSON-RPC message (MCP "streamable HTTP"). Injected so tests never touch the network.
public protocol MCPTransport: Sendable {
    func post(_ body: Data, headers: [String: String]) async throws -> MCPReply
}

public enum MCPError: Error, Equatable, Sendable {
    /// Non-2xx reply; `retryAfter` is the raw `Retry-After` header when present.
    case http(status: Int, retryAfter: String?)
    case badReply
}

/// Plain URLSession transport: ephemeral session (no cookies kept), JSON + SSE accepted.
public final class URLSessionMCPTransport: MCPTransport {
    public static let skiplaggedEndpoint = URL(string: "https://mcp.skiplagged.com/mcp")!
    public static let maxBodyBytes = 2_000_000
    private let endpoint: URL
    private let session = URLSession(configuration: .ephemeral)

    public init(endpoint: URL = URLSessionMCPTransport.skiplaggedEndpoint) {
        self.endpoint = endpoint
    }

    public func post(_ body: Data, headers: [String: String]) async throws -> MCPReply {
        var request = URLRequest(url: endpoint, timeoutInterval: 30)
        request.httpMethod = "POST"
        request.httpBody = body
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("application/json, text/event-stream", forHTTPHeaderField: "Accept")
        for (name, value) in headers { request.setValue(value, forHTTPHeaderField: name) }
        let (data, response) = try await session.data(for: request)
        guard let http = response as? HTTPURLResponse else { throw TransportError.notHTTP }
        if data.count > Self.maxBodyBytes { throw TransportError.tooLarge(data.count) }
        var lowered: [String: String] = [:]
        for (key, value) in http.allHeaderFields {
            if let key = key as? String, let value = value as? String { lowered[key.lowercased()] = value }
        }
        return MCPReply(status: http.statusCode, headers: lowered, body: data)
    }
}

/// Minimal MCP client for one server: `initialize` once (keeping `Mcp-Session-Id`),
/// `notifications/initialized`, then `tools/call`. Returns the raw JSON-RPC reply text so the
/// Rust core parses money from exact number text. Re-initializes once when the session expires.
public actor MCPClient {
    public static let protocolVersion = "2025-11-25"
    private let transport: MCPTransport
    private var sessionID: String?
    private var ready = false
    private var nextID = 1

    public init(transport: MCPTransport) {
        self.transport = transport
    }

    public func callTool(name: String, arguments: [String: Any]) async throws -> String {
        let params: [String: Any] = ["name": name, "arguments": arguments]
        try await ensureReady()
        do {
            return try await rpc("tools/call", params: params)
        } catch MCPError.http(status: 404, _) where sessionID != nil {
            ready = false
            sessionID = nil
            try await ensureReady()
            return try await rpc("tools/call", params: params)
        }
    }

    private func ensureReady() async throws {
        guard !ready else { return }
        _ = try await rpc("initialize", params: [
            "protocolVersion": Self.protocolVersion,
            "capabilities": [String: Any](),
            "clientInfo": ["name": "CheapWings", "version": "0.2"],
        ])
        _ = try await send(["jsonrpc": "2.0", "method": "notifications/initialized"])
        ready = true
    }

    /// A request with an id; returns the matching JSON-RPC message text (JSON body or SSE frame).
    private func rpc(_ method: String, params: [String: Any]) async throws -> String {
        let id = nextID
        nextID += 1
        let reply = try await send(["jsonrpc": "2.0", "id": id, "method": method, "params": params])
        if method == "initialize", let session = reply.headers["mcp-session-id"] { sessionID = session }
        guard let text = String(data: reply.body, encoding: .utf8) else { throw MCPError.badReply }
        if (reply.headers["content-type"] ?? "").contains("text/event-stream") {
            return try Self.message(inSSE: text, id: id)
        }
        return text
    }

    private func send(_ message: [String: Any]) async throws -> MCPReply {
        var headers: [String: String] = [:]
        if let sessionID { headers["Mcp-Session-Id"] = sessionID }
        if ready || message["method"] as? String == "notifications/initialized" {
            headers["MCP-Protocol-Version"] = Self.protocolVersion
        }
        let body = try JSONSerialization.data(withJSONObject: message)
        let reply = try await transport.post(body, headers: headers)
        guard (200..<300).contains(reply.status) else {
            throw MCPError.http(status: reply.status, retryAfter: reply.headers["retry-after"])
        }
        return reply
    }

    /// The `data:` payload of the SSE event whose JSON-RPC id matches (multi-line data joined).
    static func message(inSSE text: String, id: Int) throws -> String {
        let normalized = text.replacingOccurrences(of: "\r\n", with: "\n")
        for event in normalized.components(separatedBy: "\n\n") {
            let data = event.split(separator: "\n", omittingEmptySubsequences: false)
                .filter { $0.hasPrefix("data:") }
                .map { line -> String in
                    let value = line.dropFirst(5)
                    return String(value.hasPrefix(" ") ? value.dropFirst() : value)
                }
                .joined(separator: "\n")
            guard !data.isEmpty,
                  let object = try? JSONSerialization.jsonObject(with: Data(data.utf8)) as? [String: Any],
                  object["id"] as? Int == id else { continue }
            return data
        }
        throw MCPError.badReply
    }
}
