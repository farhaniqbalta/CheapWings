import CheapWingsCore
import Foundation
import Observation

public struct SkippedSearch: Sendable, Equatable {
    public let routeDate: RouteDate
    public let code: String
}

/// What an empty, finished search means — so "no flights" is never confused with a failure.
public enum EmptyOutcome: Equatable, Sendable {
    case noFlights
    case formatChanged
    case searchesFailed(Int)
}

/// Screen state for exactly one search at a time. Each start/cancel bumps `generation`, so events
/// and clean-up from an earlier search can never touch the current one, and starting again
/// cancels any search still running (never two engines → pacing holds).
@Observable @MainActor
public final class SearchSession {
    public enum Phase: Equatable, Sendable {
        case idle
        case running(done: Int, total: Int)
        case stopped(StopReason)
    }

    public private(set) var phase: Phase = .idle
    public private(set) var offers: [FoundOffer] = []
    public private(set) var failures: [SkippedSearch] = []
    /// Offers dropped by the per-offer query check, counted by reason (e.g. `currency None`).
    public private(set) var hiddenOffers: [String: Int] = [:]
    public private(set) var currency = ""

    private let engine: SearchEngine
    private var task: Task<Void, Never>?
    private var generation = 0
    private var pauseRequested = false

    /// Called once whenever a search stops for any reason (app uses it to end background work).
    public var onStop: (() -> Void)?

    public init(engine: SearchEngine) {
        self.engine = engine
    }

    public var isRunning: Bool { if case .running = phase { return true } else { return false } }

    public var emptyOutcome: EmptyOutcome? {
        guard phase == .stopped(.finished), offers.isEmpty else { return nil }
        if failures.isEmpty { return .noFlights }
        let decodeCodes: Set<String> = ["schema_changed", "partial_payload", "decode"]
        return failures.allSatisfy { decodeCodes.contains($0.code) } ? .formatChanged : .searchesFailed(failures.count)
    }

    public func start(_ request: SearchRequest, combos: [RouteDate]) {
        task?.cancel()
        generation += 1
        let current = generation
        offers = []
        failures = []
        hiddenOffers = [:]
        pauseRequested = false
        currency = request.currency
        phase = .running(done: 0, total: combos.count)
        task = Task { [engine] in
            for await event in engine.run(request, combos: combos) {
                guard current == generation else { return }
                handle(event)
            }
            if current == generation && isRunning { finish(.cancelled) }
        }
    }

    public func cancel() {
        guard isRunning else { return }
        task?.cancel()
        generation += 1
        finish(.cancelled)
    }

    /// Let the in-flight request finish, then stop as `.backgrounded` (foreground-first policy).
    public func pauseAfterCurrentRequest() {
        if isRunning { pauseRequested = true }
    }

    /// Back in the foreground before the pause took effect: keep searching.
    public func resumeIfPausePending() {
        pauseRequested = false
    }

    /// Stop now as `.backgrounded` (background time ran out).
    public func stopForBackground() {
        guard isRunning else { return }
        task?.cancel()
        generation += 1
        finish(.backgrounded)
    }

    private func finish(_ reason: StopReason) {
        phase = .stopped(reason)
        onStop?()
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
            failures.append(SkippedSearch(routeDate: combo, code: code))
        case .offersHidden(_, let reasons):
            for reason in reasons { hiddenOffers[reason, default: 0] += 1 }
        case .stopped(let reason):
            if isRunning { finish(reason) }
        }
    }
}
