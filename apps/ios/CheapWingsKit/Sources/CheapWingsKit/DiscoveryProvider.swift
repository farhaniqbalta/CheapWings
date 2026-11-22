import CheapWingsCore
import Foundation

/// One discovery call's result (P7.4). Mirrors `ProviderOutcome` without offers.
public enum DiscoveryOutcome: Sendable {
    case page(AnywherePage)
    /// This call failed; discovery continues with the other calls.
    case failed(code: String)
    /// Stop discovery (blocked, offline, cancel).
    case stop(StopReason)
    /// The source asked to wait before this call is tried again.
    case retry(after: Duration)
}

/// A source of priced destination leads for Discover. Never throws: transport errors become outcomes.
public protocol DiscoveryProvider: Sendable {
    var id: String { get }
    var pacing: ProviderPacing { get }
    func discover(_ call: DiscoveryCall, currency: String, fetchedAt: Date) async -> DiscoveryOutcome
}

/// Skiplagged's `sk_destinations_anywhere` over the same MCP client and rules as detailed search.
/// Parsing (exact USD lexemes, unpriced count, FX rate) is the Rust core's `skiplaggedAnywhere`.
public struct SkiplaggedDiscoveryProvider: DiscoveryProvider {
    public let id = "skiplagged"
    public let pacing = SkiplaggedSearchProvider().pacing
    private let client: MCPClient

    public init(transport: MCPTransport = URLSessionMCPTransport()) {
        client = MCPClient(transport: transport)
    }

    static func arguments(_ call: DiscoveryCall, currency: String) -> [String: Any] {
        ["from": call.origin, "depart": call.date, "currency": currency, "fare_class": "economy", "adults": 1]
    }

    public func discover(_ call: DiscoveryCall, currency: String, fetchedAt: Date) async -> DiscoveryOutcome {
        let raw: String
        do {
            raw = try await client.callTool(name: "sk_destinations_anywhere", arguments: Self.arguments(call, currency: currency))
        } catch {
            switch SkiplaggedSearchProvider.outcome(for: error) {
            case .retry(let after): return .retry(after: after)
            case .stop(let reason): return .stop(reason)
            case .failed(let code, _): return .failed(code: code)
            case .found: return .failed(code: "network")
            }
        }
        if Task.isCancelled { return .stop(.cancelled) }
        do {
            return .page(try skiplaggedAnywhere(rpcJson: raw, origin: call.origin, depart: call.date,
                                                fetchedAt: fetchedAt.formatted(.iso8601)))
        } catch SkiplaggedError.Failed(let code, _) {
            return .failed(code: code)
        } catch {
            return .failed(code: "schema_changed")
        }
    }
}
