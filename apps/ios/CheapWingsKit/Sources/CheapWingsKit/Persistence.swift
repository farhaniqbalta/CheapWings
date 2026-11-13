import CheapWingsCore
import Foundation

/// What the session needs from on-device storage. `SearchStore` (Rust, SQLite) is the real one;
/// tests inject failing stores to prove a broken store never stops a search.
public protocol SearchPersistence: AnyObject {
    func createSearch(request: StoredRequest, combos: [RouteDate], nowMs: Int64) throws -> Int64
    func finishCombo(searchId: Int64, index: UInt32, offers: [FliOffer], hidden: [String], failure: String?, nowMs: Int64) throws
    func setStopped(searchId: Int64, reason: String, nowMs: Int64) throws
    func clearStopped(searchId: Int64) throws
    func latest() throws -> StoredSearch?
    func pending(searchId: Int64) throws -> [StoredCombo]
}

extension SearchStore: SearchPersistence {}

extension StopReason {
    /// Text form kept in the store (`finished | cancelled | rate_limited | blocked:<detail> | backgrounded | interrupted`).
    var storedText: String {
        switch self {
        case .finished: return "finished"
        case .cancelled: return "cancelled"
        case .rateLimited: return "rate_limited"
        case .blocked(let detail): return "blocked:\(detail)"
        case .backgrounded: return "backgrounded"
        case .interrupted: return "interrupted"
        }
    }

    init?(storedText text: String) {
        switch text {
        case "finished": self = .finished
        case "cancelled": self = .cancelled
        case "rate_limited": self = .rateLimited
        case "backgrounded": self = .backgrounded
        case "interrupted": self = .interrupted
        default:
            guard text.hasPrefix("blocked:") else { return nil }
            self = .blocked(String(text.dropFirst("blocked:".count)))
        }
    }

    /// Google asked us to stop: no one-tap resume for a while.
    var isProviderStop: Bool {
        switch self {
        case .rateLimited, .blocked: return true
        default: return false
        }
    }
}

extension SearchRequest {
    var stored: StoredRequest {
        StoredRequest(origins: origins, destinations: destinations, dateFrom: dateFrom, dateThrough: dateThrough,
                      currency: currency, maxStops: maxStops, originMajor: originMajorID, destinationMajor: destinationMajorID)
    }

    init(stored: StoredRequest) {
        self.init(origins: stored.origins, destinations: stored.destinations, dateFrom: stored.dateFrom,
                  dateThrough: stored.dateThrough, currency: stored.currency, maxStops: stored.maxStops,
                  originMajorID: stored.originMajor, destinationMajorID: stored.destinationMajor)
    }
}

extension Date {
    var milliseconds: Int64 { Int64((timeIntervalSince1970 * 1000).rounded()) }
    init(milliseconds: Int64) { self.init(timeIntervalSince1970: Double(milliseconds) / 1000) }
}
