import CheapWingsCore
import CheapWingsKit
import Foundation
import Observation
import UIKit

/// The search form plus iOS lifecycle glue. Search state lives in `SearchSession`
/// (CheapWingsKit, unit-tested); planning and ranking come from the Rust core.
@Observable @MainActor
final class SearchModel {
    static let currencies = ["IDR", "USD", "AUD", "JPY"]

    var originsText = "CGK"
    var destinationsText = "DPS"
    var dateFrom = Calendar.current.date(byAdding: .day, value: 30, to: .now)!
    var dateThrough = Calendar.current.date(byAdding: .day, value: 32, to: .now)!
    var currency = "IDR"

    let session = SearchSession(engine: SearchEngine(transport: URLSessionFliTransport()))
    private var backgroundTask: UIBackgroundTaskIdentifier = .invalid

    init() {
        session.onStop = { [weak self] in self?.endBackgroundTask() }
    }

    var request: SearchRequest {
        SearchRequest(origins: Self.codes(originsText), destinations: Self.codes(destinationsText),
                      dateFrom: Self.ymd(dateFrom), dateThrough: Self.ymd(dateThrough), currency: currency)
    }

    /// Re-planned on every edit, so the form shows the count or the reason before any request.
    var plan: Result<[RouteDate], Error> { Result { try request.plan() } }

    var planSummary: String {
        switch plan {
        case .success(let combos): return "\(combos.count) route/date searches · 1 per second"
        case .failure(PlanSearchError.Rejected(_, let detail)): return detail.prefix(1).uppercased() + detail.dropFirst()
        case .failure(let error): return "\(error)"
        }
    }

    var canSearch: Bool { !session.isRunning && (try? plan.get()) != nil }

    func start() {
        guard canSearch, let combos = try? plan.get() else { return }
        session.start(request, combos: combos)
    }

    /// Foreground-first (P5.05 §5): the in-flight request may finish, then the search stops.
    func appBackgrounded() {
        guard session.isRunning else { return }
        session.pauseAfterCurrentRequest()
        guard backgroundTask == .invalid else { return }  // one background task at a time
        backgroundTask = UIApplication.shared.beginBackgroundTask(withName: "Finish current flight search request") { [weak self] in
            // Expiration runs on the main thread; stop and end the task before returning.
            MainActor.assumeIsolated {
                self?.session.stopForBackground()
                self?.endBackgroundTask()
            }
        }
    }

    func appForegrounded() {
        session.resumeIfPausePending()
        endBackgroundTask()
    }

    private func endBackgroundTask() {
        guard backgroundTask != .invalid else { return }
        UIApplication.shared.endBackgroundTask(backgroundTask)
        backgroundTask = .invalid
    }

    static func codes(_ text: String) -> [String] {
        text.split(whereSeparator: { $0 == "," || $0.isWhitespace }).map(String.init)
    }

    static func ymd(_ date: Date) -> String {
        let c = Calendar.current.dateComponents([.year, .month, .day], from: date)
        return String(format: "%04d-%02d-%02d", c.year!, c.month!, c.day!)
    }
}
