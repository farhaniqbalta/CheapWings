import CheapWingsCore
import Foundation
import os

/// One-way flag shared between request tasks and the launcher.
final class StopFlag: Sendable {
    private let lock = OSAllocatedUnfairLock(initialState: false)
    var isSet: Bool { lock.withLock { $0 } }
    func set() { lock.withLock { $0 = true } }
}

/// Provider-neutral pacing (the web's start-to-start logic): a request starts at least
/// `pacing.interval` after the previous start, at most `pacing.maxInFlight` are open, and results
/// are released in plan order so checkpoints, the date strip and Resume see the same sequence as
/// a one-at-a-time search. A slot frees when its result is released (not when it arrives), and a
/// stop on route/date k releases nothing for k or later — those stay pending for Resume.
enum PacedRunner {
    static func execute(provider: SearchProvider, request: SearchRequest, combos: [RouteDate],
                        sleep: @Sendable (Duration) async throws -> Void,
                        out: AsyncStream<SearchEvent>.Continuation) async {
        func stop(_ reason: StopReason) {
            out.yield(.stopped(reason))
            out.finish()
        }
        out.yield(.started(total: combos.count))
        let pacing = provider.pacing
        // Set by a request the moment it comes back with a stop (429, block, offline…), so no new
        // request starts after the provider said stop — even before that reply can be released.
        let stopSeen = StopFlag()
        await withTaskGroup(of: (Int, ProviderOutcome).self) { group in
            var nextToStart = 0, nextToRelease = 0
            var arrived: [Int: ProviderOutcome] = [:]
            while nextToRelease < combos.count {
                // Start as many as pacing allows; replies that land meanwhile wait in the group.
                while nextToStart < combos.count, nextToStart - nextToRelease < pacing.maxInFlight, !stopSeen.isSet {
                    if nextToStart > 0 {
                        do { try await sleep(pacing.interval) } catch { group.cancelAll(); return stop(.cancelled) }
                    }
                    if Task.isCancelled { group.cancelAll(); return stop(.cancelled) }
                    if stopSeen.isSet { break }
                    let index = nextToStart, combo = combos[index]
                    group.addTask {
                        let outcome = await provider.search(combo, request: request)
                        if case .stop = outcome { stopSeen.set() }
                        return (index, outcome)
                    }
                    nextToStart += 1
                }
                guard let (index, outcome) = await group.next() else { break }
                arrived[index] = outcome
                while let outcome = arrived.removeValue(forKey: nextToRelease) {
                    if Task.isCancelled { group.cancelAll(); return stop(.cancelled) }  // never deliver after cancel
                    let combo = combos[nextToRelease]
                    switch outcome {
                    case .stop(let reason):
                        group.cancelAll()
                        return stop(reason)
                    case .found(let offers, let hidden):
                        if !offers.isEmpty { out.yield(.offers(offers)) }
                        if !hidden.isEmpty { out.yield(.offersHidden(combo, reasons: hidden)) }
                    case .failed(let code, let hidden):
                        out.yield(.comboFailed(combo, code: code))
                        if !hidden.isEmpty { out.yield(.offersHidden(combo, reasons: hidden)) }
                    }
                    nextToRelease += 1
                    out.yield(.progress(done: nextToRelease, total: combos.count))
                }
            }
            if Task.isCancelled { return stop(.cancelled) }
            stop(.finished)
        }
    }
}
