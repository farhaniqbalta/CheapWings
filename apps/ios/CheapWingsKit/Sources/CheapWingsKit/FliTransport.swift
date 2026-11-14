import Foundation

/// What one Fli page fetch produced. `refusedRedirect` is set when the redirect policy stopped
/// a redirect (e.g. to `google.com/sorry` or a consent page); the response is then that 3xx.
public struct FetchedPage: Sendable {
    public let status: Int
    public let body: Data
    public let refusedRedirect: URL?

    public init(status: Int, body: Data, refusedRedirect: URL?) {
        self.status = status
        self.body = body
        self.refusedRedirect = refusedRedirect
    }
}

public protocol FliTransport: Sendable {
    func fetch(_ url: URL) async throws -> FetchedPage
}

public enum TransportError: Error, Sendable {
    case tooLarge(Int)
    case notHTTP
}

/// Redirect rule from `providers/fli.py`: only https www.google.com/travel/flights*, never /unsupported.
public func isAllowedFliRedirect(_ url: URL) -> Bool {
    url.scheme == "https" && url.host == "www.google.com"
        && url.path.hasPrefix("/travel/flights") && !url.path.hasSuffix("/unsupported")
}

/// The request shape proven on iPad in P5.06 S1: platform TLS, Safari-iPad User-Agent,
/// ephemeral session (no cookies carried between searches), no challenge handling.
public final class URLSessionFliTransport: FliTransport {
    public static let userAgent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Safari/605.1.15"
    public static let maxBodyBytes = 8_000_000
    private let session: URLSession = {
        let configuration = URLSessionConfiguration.ephemeral
        // iOS allows 4 per host by default; Fli pacing keeps up to 6 open (P5.8).
        configuration.httpMaximumConnectionsPerHost = ProviderPacing.fli.maxInFlight
        return URLSession(configuration: configuration)
    }()

    public init() {}

    public func fetch(_ url: URL) async throws -> FetchedPage {
        var request = URLRequest(url: url, timeoutInterval: 25)
        request.setValue(Self.userAgent, forHTTPHeaderField: "User-Agent")
        request.setValue("text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", forHTTPHeaderField: "Accept")
        request.setValue("en-US,en;q=0.9", forHTTPHeaderField: "Accept-Language")
        let policy = RedirectPolicy()
        let (data, response) = try await session.data(for: request, delegate: policy)
        guard let http = response as? HTTPURLResponse else { throw TransportError.notHTTP }
        guard data.count <= Self.maxBodyBytes else { throw TransportError.tooLarge(data.count) }
        return FetchedPage(status: http.statusCode, body: data, refusedRedirect: policy.refused)
    }
}

/// Per-request delegate: follows only allowed redirects and remembers the first refused one.
private final class RedirectPolicy: NSObject, URLSessionTaskDelegate, @unchecked Sendable {
    private let lock = NSLock()
    private var _refused: URL?
    var refused: URL? { lock.withLock { _refused } }

    func urlSession(_ session: URLSession, task: URLSessionTask, willPerformHTTPRedirection response: HTTPURLResponse,
                    newRequest request: URLRequest, completionHandler: @escaping (URLRequest?) -> Void) {
        if let url = request.url, isAllowedFliRedirect(url) {
            completionHandler(request)
        } else {
            lock.withLock { _refused = request.url }
            completionHandler(nil)  // never follow to /sorry or consent
        }
    }
}
