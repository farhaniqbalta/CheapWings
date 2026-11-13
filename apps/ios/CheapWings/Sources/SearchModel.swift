import BackgroundTasks
import CheapWingsCore
import CheapWingsKit
import Foundation
import Observation
import UIKit

/// The search form plus iOS lifecycle glue. Search state lives in `SearchSession`
/// (CheapWingsKit, unit-tested); planning, ranking and storage are the Rust core's.
@Observable @MainActor
final class SearchModel {
    static let currencies = ["IDR", "USD", "AUD", "JPY"]

    var originsText = "CGK"
    var destinationsText = "DPS"
    var dateFrom = Calendar.current.date(byAdding: .day, value: 30, to: .now)!
    var dateThrough = Calendar.current.date(byAdding: .day, value: 32, to: .now)!
    var currency = "IDR"

    let session: SearchSession
    /// Set when the on-device history could not be opened (search still works).
    let historyError: String?
    private var backgroundTask: UIBackgroundTaskIdentifier = .invalid
    /// The system continued-processing task while one is attached (iOS 26+), typed loosely so the
    /// model compiles for iOS 17.
    private var continuedTask: AnyObject?

    init() {
        let engine = SearchEngine(transport: URLSessionFliTransport())
        let store: SearchStore?
        let openError: String?
        do {
            store = try Self.openStore()
            openError = nil
        } catch {
            store = nil
            openError = "Search history unavailable: \(error)"
        }
        historyError = openError
        session = SearchSession(engine: engine, store: store)
        session.onStop = { [weak self] in self?.searchStopped() }
        session.restoreLatest()
        if let request = session.request { fillForm(from: request) }
        if #available(iOS 26.0, *) { ContinuedSearch.onTask = { [weak self] task in self?.attach(task) } }
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
        requestContinuedProcessing()
    }

    func resume() {
        guard session.canResume else { return }
        session.resume()
        if session.isRunning { requestContinuedProcessing() }
    }

    // MARK: - Lifecycle

    /// Foreground-first (P5.05 §5) unless iOS is already continuing the search for us.
    func appBackgrounded() {
        guard session.isRunning, continuedTask == nil else { return }
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

    /// Mirrors search progress into the system's continued-processing UI.
    func progressChanged() {
        guard #available(iOS 26.0, *), let task = continuedTask as? BGContinuedProcessingTask,
              case .running(let done, let total) = session.phase else { return }
        task.progress.totalUnitCount = Int64(total)
        task.progress.completedUnitCount = Int64(done)
    }

    @available(iOS 26.0, *)
    func attach(_ task: BGContinuedProcessingTask) {
        guard session.isRunning else { return task.setTaskCompleted(success: false) }
        continuedTask = task
        progressChanged()
        task.expirationHandler = { [weak self] in
            // The user cancelled in system UI or iOS needs the resources: stop (already checkpointed).
            Task { @MainActor in self?.session.stopForBackground() }
        }
    }

    private func requestContinuedProcessing() {
        guard #available(iOS 26.0, *), let running = session.request,
              case .running(let done, let total) = session.phase else { return }
        let route = "\(running.origins.joined(separator: ","))→\(running.destinations.joined(separator: ","))"
        _ = ContinuedSearch.submit(title: "Searching \(route)", subtitle: "\(done) of \(total) route/date searches")
    }

    private func searchStopped() {
        endBackgroundTask()
        if #available(iOS 26.0, *), let task = continuedTask as? BGContinuedProcessingTask {
            task.setTaskCompleted(success: session.phase == .stopped(.finished))
        }
        continuedTask = nil
    }

    private func endBackgroundTask() {
        guard backgroundTask != .invalid else { return }
        UIApplication.shared.endBackgroundTask(backgroundTask)
        backgroundTask = .invalid
    }

    // MARK: - Helpers

    private func fillForm(from request: SearchRequest) {
        originsText = request.origins.joined(separator: ", ")
        destinationsText = request.destinations.joined(separator: ", ")
        currency = request.currency
        if let from = Self.date(request.dateFrom), let through = Self.date(request.dateThrough) {
            dateFrom = from
            dateThrough = through
        }
    }

    /// `Application Support/CheapWings/searches.sqlite`, readable after first unlock so the
    /// store keeps working while a search continues in the background.
    static func openStore() throws -> SearchStore {
        let support = try FileManager.default.url(for: .applicationSupportDirectory, in: .userDomainMask,
                                                  appropriateFor: nil, create: true)
        let dir = support.appendingPathComponent("CheapWings", isDirectory: true)
        let protection: [FileAttributeKey: Any] = [.protectionKey: FileProtectionType.completeUntilFirstUserAuthentication]
        try FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true, attributes: protection)
        let file = dir.appendingPathComponent("searches.sqlite")
        let store = try SearchStore(path: file.path)
        try? FileManager.default.setAttributes(protection, ofItemAtPath: file.path)
        return store
    }

    static func codes(_ text: String) -> [String] {
        text.split(whereSeparator: { $0 == "," || $0.isWhitespace }).map(String.init)
    }

    static func ymd(_ date: Date) -> String {
        let c = Calendar.current.dateComponents([.year, .month, .day], from: date)
        return String(format: "%04d-%02d-%02d", c.year!, c.month!, c.day!)
    }

    static func date(_ ymd: String) -> Date? {
        let parts = ymd.split(separator: "-").compactMap { Int($0) }
        guard parts.count == 3 else { return nil }
        return Calendar.current.date(from: DateComponents(year: parts[0], month: parts[1], day: parts[2]))
    }
}
