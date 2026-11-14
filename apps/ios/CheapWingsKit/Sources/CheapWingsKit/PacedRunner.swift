import CheapWingsCore
import Foundation
import os

/// One-way flag shared between request tasks and the launcher.
final class StopFlag: Sendable {
    private let lock = OSAllocatedUnfairLock(initialState: false)
    var isSet: Bool { lock.withLock { $0 } }
    func set() { lock.withLock { $0 = true } }
}

/// A lane-wide "wait until" set by a retry-after reply, so the lane starts nothing new meanwhile.
final class LanePause: Sendable {
    private let lock = OSAllocatedUnfairLock<ContinuousClock.Instant?>(initialState: nil)
    func extend(by duration: Duration) {
        let until = ContinuousClock.now + duration
        lock.withLock { current in if current.map({ until > $0 }) ?? true { current = until } }
    }
    var remaining: Duration? {
        lock.withLock { until in until.map { $0 - ContinuousClock.now } }.flatMap { $0 > .zero ? $0 : nil }
    }
}

/// Serialises output: each finished item's events are yielded in one go, so lanes never
/// interleave inside an item, and the progress count is shared.
actor RunEmitter {
    private let out: AsyncStream<SearchEvent>.Continuation
    private let total: Int
    private var done = 0

    init(out: AsyncStream<SearchEvent>.Continuation, total: Int) {
        self.out = out
        self.total = total
    }

    func item(_ index: Int, _ combo: RouteDate, _ outcome: ProviderOutcome) {
        out.yield(.item(index))
        switch outcome {
        case .found(let offers, let hidden):
            if !offers.isEmpty { out.yield(.offers(offers)) }
            if !hidden.isEmpty { out.yield(.offersHidden(combo, reasons: hidden)) }
        case .failed(let code, let hidden):
            out.yield(.comboFailed(combo, code: code))
            if !hidden.isEmpty { out.yield(.offersHidden(combo, reasons: hidden)) }
        case .retry:
            out.yield(.comboFailed(combo, code: "http_rate_limited"))
        case .stop:
            break
        }
        done += 1
        out.yield(.progress(done: done, total: total))
    }

    func providerStopped(_ provider: String, _ reason: StopReason) {
        out.yield(.providerStopped(provider, reason))
    }
}

/// Provider-neutral pacing (the web's start-to-start logic), one lane per provider: a request
/// starts at least `pacing.interval` after the lane's previous start, at most
/// `pacing.maxInFlight` are open, and results are released in the lane's order. A slot frees
/// when its result is released; a stop on item k releases nothing for k or later in that lane
/// (they stay pending for Resume). A retry-after reply pauses the lane and retries that item,
/// at most 3 attempts (then, or for a wait over 2 min, the source stops as rate-limited). Offline or cancel stops every lane; a provider stop only its own.
enum PacedRunner {
    static let maxAttempts = 3
    /// Longer Retry-After waits stop the source instead of sleeping silently.
    static let maxRetryWait: Duration = .seconds(120)

    static func execute(providers: [SearchProvider], request: SearchRequest, items: [WorkItem],
                        sleep: @escaping @Sendable (Duration) async throws -> Void,
                        out: AsyncStream<SearchEvent>.Continuation) async {
        out.yield(.started(total: items.count))
        let emitter = RunEmitter(out: out, total: items.count)
        let lanes: [(SearchProvider, [(Int, RouteDate)])] = providers.compactMap { provider in
            let mine = items.enumerated().filter { $0.element.provider == provider.id }.map { ($0.offset, $0.element.routeDate) }
            return mine.isEmpty ? nil : (provider, mine)
        }
        var reasons: [StopReason] = []
        await withTaskGroup(of: (String, StopReason?).self) { group in
            for (provider, laneItems) in lanes {
                group.addTask {
                    (provider.id, await lane(provider, request: request, items: laneItems, sleep: sleep, emitter: emitter))
                }
            }
            for await (provider, reason) in group {
                guard let reason else { continue }
                reasons.append(reason)
                switch reason {
                case .offline:
                    group.cancelAll()  // the device is offline: every lane pauses
                case .cancelled:
                    break
                default:
                    await emitter.providerStopped(provider, reason)
                }
            }
        }
        let final: StopReason
        if Task.isCancelled {
            final = .cancelled
        } else if reasons.contains(.offline) {
            final = .offline
        } else if let stop = reasons.first(where: { $0 != .cancelled }) {
            final = stop
        } else if reasons.contains(.cancelled) {
            final = .cancelled
        } else {
            final = .finished
        }
        out.yield(.stopped(final))
        out.finish()
    }

    /// Runs one provider over its items (`(global index, route/date)`); nil when every item finished.
    static func lane(_ provider: SearchProvider, request: SearchRequest, items: [(Int, RouteDate)],
                     sleep: @escaping @Sendable (Duration) async throws -> Void, emitter: RunEmitter) async -> StopReason? {
        let pacing = provider.pacing
        // Set by a request the moment it comes back with a stop, so no new request starts after
        // the provider said stop — even before that reply can be released.
        let stopSeen = StopFlag()
        let pause = LanePause()
        return await withTaskGroup(of: (Int, ProviderOutcome).self) { group -> StopReason? in
            var nextToStart = 0, nextToRelease = 0
            var arrived: [Int: ProviderOutcome] = [:]
            while nextToRelease < items.count {
                while nextToStart < items.count, nextToStart - nextToRelease < pacing.maxInFlight, !stopSeen.isSet {
                    do {
                        if nextToStart > 0 { try await sleep(pacing.interval) }
                        if let wait = pause.remaining { try await sleep(wait) }
                    } catch {
                        group.cancelAll()
                        return .cancelled
                    }
                    if Task.isCancelled { group.cancelAll(); return .cancelled }
                    if stopSeen.isSet { break }
                    let position = nextToStart, combo = items[position].1
                    group.addTask {
                        var attempts = 0
                        while true {
                            let outcome = await provider.search(combo, request: request)
                            if case .retry(let after) = outcome {
                                attempts += 1
                                // Still limited after 3 tries, or asked to wait long: stop this source
                                // (its days stay pending, cooldown applies) — never burn the rest.
                                if attempts >= maxAttempts || after > maxRetryWait {
                                    stopSeen.set()
                                    return (position, .stop(.rateLimited))
                                }
                                pause.extend(by: after)
                                do { try await sleep(after) } catch { return (position, .stop(.cancelled)) }
                                if Task.isCancelled { return (position, .stop(.cancelled)) }
                                continue
                            }
                            if case .stop = outcome { stopSeen.set() }
                            return (position, outcome)
                        }
                    }
                    nextToStart += 1
                }
                guard let (position, outcome) = await group.next() else { break }
                arrived[position] = outcome
                while let outcome = arrived.removeValue(forKey: nextToRelease) {
                    if Task.isCancelled { group.cancelAll(); return .cancelled }  // never deliver after cancel
                    if case .stop(let reason) = outcome {
                        group.cancelAll()
                        return reason
                    }
                    let (index, combo) = items[nextToRelease]
                    await emitter.item(index, combo, outcome)
                    nextToRelease += 1
                }
            }
            return Task.isCancelled ? .cancelled : nil
        }
    }
}
