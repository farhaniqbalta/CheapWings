import CheapWingsCore
import CheapWingsKit
import Foundation
import Observation
import UIKit

/// UI state for one on-device Fli search. Planning and ranking come from the Rust core via
/// CheapWingsKit; this class only tracks what the screen shows.
@Observable @MainActor
final class SearchModel {
    enum Phase: Equatable {
        case idle
        case running(done: Int, total: Int)
        case stopped(StopReason)
    }

    static let currencies = ["IDR", "USD", "AUD", "JPY"]

    var originsText = "CGK"
    var destinationsText = "DPS"
    var dateFrom = Calendar.current.date(byAdding: .day, value: 30, to: .now)!
    var dateThrough = Calendar.current.date(byAdding: .day, value: 32, to: .now)!
    var currency = "IDR"

    private(set) var phase: Phase = .idle
    private(set) var offers: [FoundOffer] = []
    private(set) var failures: [(RouteDate, String)] = []

    private let engine = SearchEngine(transport: URLSessionFliTransport())
    private var task: Task<Void, Never>?
    private var pauseRequested = false
    private var backgroundTask: UIBackgroundTaskIdentifier = .invalid

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

    var isRunning: Bool { if case .running = phase { return true } else { return false } }
    var canSearch: Bool { !isRunning && (try? plan.get()) != nil }

    /// Every page failed to decode or check: say so instead of looking like "no flights".
    var allFailed: Bool { phase == .stopped(.finished) && offers.isEmpty && !failures.isEmpty }

    func start() {
        guard canSearch, let combos = try? plan.get() else { return }
        offers = []
        failures = []
        pauseRequested = false
        phase = .running(done: 0, total: combos.count)
        let request = request
        task = Task { [engine] in
            for await event in engine.run(request, combos: combos) {
                handle(event)
            }
            if isRunning { phase = .stopped(.cancelled) }
            endBackgroundTask()
        }
    }

    func cancel() {
        task?.cancel()
        phase = .stopped(.cancelled)
    }

    /// Foreground-first (P5.05 §5): keep running long enough for the in-flight request to finish,
    /// then stop. No resume in P5.2.
    func appBackgrounded() {
        guard isRunning else { return }
        pauseRequested = true
        backgroundTask = UIApplication.shared.beginBackgroundTask(withName: "Finish current flight search request") { [weak self] in
            Task { @MainActor in self?.stopForBackground() }
        }
    }

    func appForegrounded() {
        guard isRunning else { return }
        pauseRequested = false
        endBackgroundTask()
    }

    private func handle(_ event: SearchEvent) {
        switch event {
        case .started(let total):
            phase = .running(done: 0, total: total)
        case .progress(let done, let total):
            phase = .running(done: done, total: total)
            if pauseRequested { stopForBackground() }
        case .offers(let found):
            offers = rankLowestAdvertised(offers + found)
        case .comboFailed(let combo, let code):
            failures.append((combo, code))
        case .stopped(let reason):
            if isRunning { phase = .stopped(reason) }
        }
    }

    private func stopForBackground() {
        task?.cancel()
        phase = .stopped(.backgrounded)
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
