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

/// A stored search that stopped before every route/date finished.
public struct ResumeInfo: Equatable, Sendable {
    public let request: SearchRequest
    public let total: Int
    public let done: Int
    public let stopReason: StopReason
    public let stoppedAt: Date
}

/// Screen state for exactly one search at a time. Each start/cancel bumps `generation`, so events
/// and clean-up from an earlier search can never touch the current one, and starting again
/// cancels any search still running (never two engines → pacing holds). With a store, every
/// finished route/date is checkpointed and an interrupted search can be resumed.
@Observable @MainActor
public final class SearchSession {
    public enum Phase: Equatable, Sendable {
        case idle
        case running(done: Int, total: Int)
        case stopped(StopReason)
    }

    /// No one-tap resume this soon after Google rate-limited or blocked us.
    public static let providerStopCooldown: TimeInterval = 30 * 60

    public private(set) var phase: Phase = .idle
    public private(set) var offers: [FoundOffer] = []
    public private(set) var failures: [SkippedSearch] = []
    /// Offers dropped by the per-offer query check, counted by reason (e.g. `currency None`).
    public private(set) var hiddenOffers: [String: Int] = [:]
    public private(set) var currency = ""
    /// Set when on-device history failed; searching continues without it.
    public private(set) var storeError: String?
    public private(set) var resumable: ResumeInfo?

    private let engine: SearchEngine
    private let store: SearchPersistence?
    private let now: @Sendable () -> Date
    private var task: Task<Void, Never>?
    private var generation = 0
    private var pauseRequested = false

    // The search being shown/run.
    private var searchID: Int64?
    /// The request of the search being shown (new, running or restored).
    public private(set) var request: SearchRequest?
    private var total = 0
    private var doneBefore = 0
    private var run: [(index: UInt32, routeDate: RouteDate)] = []
    // Outcome of the route/date in flight, saved when it finishes.
    private var inFlightOffers: [FliOffer] = []
    private var inFlightHidden: [String] = []
    private var inFlightFailure: String?

    /// Called once whenever a search stops for any reason (app uses it to end background work).
    public var onStop: (() -> Void)?

    public init(engine: SearchEngine, store: SearchPersistence? = nil, now: @escaping @Sendable () -> Date = { Date() }) {
        self.engine = engine
        self.store = store
        self.now = now
    }

    public var isRunning: Bool { if case .running = phase { return true } else { return false } }

    public var emptyOutcome: EmptyOutcome? {
        guard phase == .stopped(.finished), offers.isEmpty else { return nil }
        if failures.isEmpty { return .noFlights }
        let decodeCodes: Set<String> = ["schema_changed", "partial_payload", "decode"]
        return failures.allSatisfy { decodeCodes.contains($0.code) } ? .formatChanged : .searchesFailed(failures.count)
    }

    /// When Google stopped the search, resume waits for the cooldown.
    public var resumeAllowedAfter: Date? {
        guard let info = resumable, info.stopReason.isProviderStop else { return nil }
        return info.stoppedAt.addingTimeInterval(Self.providerStopCooldown)
    }

    public var canResume: Bool {
        guard resumable != nil, !isRunning else { return false }
        if let after = resumeAllowedAfter { return now() >= after }
        return true
    }

    // MARK: - Starting, resuming, stopping

    public func start(_ request: SearchRequest, combos: [RouteDate]) {
        offers = []
        failures = []
        hiddenOffers = [:]
        resumable = nil
        searchID = nil
        if let store {
            do { searchID = try store.createSearch(request: request.stored, combos: combos, nowMs: now().milliseconds) }
            catch { record(error) }
        }
        launch(request, run: combos.enumerated().map { (UInt32($0.offset), $0.element) }, total: combos.count, doneBefore: 0)
    }

    /// Shows the newest stored search (offers, failures, how far it got). Call at launch.
    public func restoreLatest() {
        guard let store, !isRunning else { return }
        let stored: StoredSearch
        do {
            guard let latest = try store.latest() else { return }
            stored = latest
        } catch {
            return record(error)
        }
        let request = SearchRequest(stored: stored.request)
        self.request = request
        searchID = stored.id
        total = stored.combos.count
        currency = request.currency
        offers = rankLowestAdvertised(stored.offers.compactMap { item in
            guard Int(item.comboIndex) < stored.combos.count else { return nil }
            let combo = stored.combos[Int(item.comboIndex)].routeDate
            return FoundOffer(routeDate: combo, index: Int(item.offerIndex), offer: item.offer,
                              searchURL: request.searchURL(combo), fetchedAt: Date(milliseconds: item.fetchedAtMs))
        })
        failures = stored.combos.filter { $0.status == .failed }.map { SkippedSearch(routeDate: $0.routeDate, code: $0.code ?? "failed") }
        hiddenOffers = Dictionary(stored.hidden.map { ($0.reason, Int($0.count)) }, uniquingKeysWith: +)
        let done = stored.combos.filter { $0.status != .pending }.count
        let reason = stored.stopReason.flatMap(StopReason.init(storedText:)) ?? (done == total ? .finished : .interrupted)
        phase = .stopped(reason)
        resumable = done < total
            ? ResumeInfo(request: request, total: total, done: done, stopReason: reason, stoppedAt: Date(milliseconds: stored.updatedAtMs))
            : nil
    }

    /// Runs only the route/dates the stored search has not finished, with its stored request.
    public func resume() {
        guard canResume, let info = resumable, let store, let id = searchID else { return }
        let pending: [StoredCombo]
        do { pending = try store.pending(searchId: id) } catch { return record(error) }
        guard !pending.isEmpty else { resumable = nil; return }
        do { try store.clearStopped(searchId: id) } catch { record(error) }
        launch(info.request, run: pending.map { ($0.index, $0.routeDate) }, total: info.total, doneBefore: info.total - pending.count)
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

    // MARK: - Internals

    private func launch(_ request: SearchRequest, run: [(index: UInt32, routeDate: RouteDate)], total: Int, doneBefore: Int) {
        task?.cancel()
        generation += 1
        let current = generation
        self.request = request
        self.run = run
        self.total = total
        self.doneBefore = doneBefore
        resetInFlight()
        pauseRequested = false
        currency = request.currency
        phase = .running(done: doneBefore, total: total)
        let combos = run.map(\.routeDate)
        task = Task { [engine] in
            for await event in engine.run(request, combos: combos) {
                guard current == generation else { return }
                handle(event)
            }
            if current == generation && isRunning { finish(.cancelled) }
        }
    }

    private func finish(_ reason: StopReason) {
        let done = doneSoFar  // read before `phase` changes: it holds the live count
        phase = .stopped(reason)
        if let request, done < total {
            resumable = ResumeInfo(request: request, total: total, done: done, stopReason: reason, stoppedAt: now())
        } else {
            resumable = nil
        }
        if let store, let id = searchID {
            do { try store.setStopped(searchId: id, reason: reason.storedText, nowMs: now().milliseconds) }
            catch { record(error) }
        }
        onStop?()
    }

    private var doneSoFar: Int {
        if case .running(let done, _) = phase { return done }
        return resumable?.done ?? doneBefore + finishedInRun
    }

    private var finishedInRun = 0

    private func handle(_ event: SearchEvent) {
        switch event {
        case .started:
            finishedInRun = 0
            phase = .running(done: doneBefore, total: total)
        case .progress(let done, _):
            // The engine emits exactly one progress per finished route/date: checkpoint it.
            checkpoint(runIndex: done - 1)
            finishedInRun = done
            phase = .running(done: doneBefore + done, total: total)
            if pauseRequested { stopForBackground() }
        case .offers(let found):
            inFlightOffers += found.map(\.offer)
            offers = rankLowestAdvertised(offers + found)
        case .comboFailed(let combo, let code):
            inFlightFailure = code
            failures.append(SkippedSearch(routeDate: combo, code: code))
        case .offersHidden(_, let reasons):
            inFlightHidden += reasons
            for reason in reasons { hiddenOffers[reason, default: 0] += 1 }
        case .stopped(let reason):
            if isRunning { finish(reason) }
        }
    }

    private func checkpoint(runIndex: Int) {
        defer { resetInFlight() }
        guard let store, let id = searchID, run.indices.contains(runIndex) else { return }
        do {
            try store.finishCombo(searchId: id, index: run[runIndex].index, offers: inFlightOffers,
                                  hidden: inFlightHidden, failure: inFlightFailure, nowMs: now().milliseconds)
        } catch {
            record(error)
        }
    }

    private func resetInFlight() {
        inFlightOffers = []
        inFlightHidden = []
        inFlightFailure = nil
    }

    private func record(_ error: Error) {
        storeError = "Search history unavailable: \(error)"
    }
}
