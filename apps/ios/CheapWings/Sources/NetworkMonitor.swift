import Network
import Observation

/// Whether the device has a usable internet path, for the form and the Resume button.
/// The engine still decides from real request errors (a path can be "satisfied" yet fail).
@Observable @MainActor
final class NetworkMonitor {
    private(set) var isOnline = true
    private let monitor = NWPathMonitor()

    init() {
        monitor.pathUpdateHandler = { [weak self] path in
            let online = path.status == .satisfied
            Task { @MainActor in self?.isOnline = online }
        }
        monitor.start(queue: DispatchQueue(label: "dev.cheapwings.network"))
    }

    deinit { monitor.cancel() }
}
