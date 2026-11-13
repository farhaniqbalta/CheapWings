// Offline iOS-simulator check (no network): does wreq's Chrome client build on iOS?
// wreq #1089 reported `boring tls error: ErrorStack([])` at exactly this step on an iOS 26 simulator.
import Foundation

if let error = wreqClientBuilds() {
    print("wreq client build on iOS FAILED: \(error)")
    exit(1)
}
print("wreq client build on iOS OK")
