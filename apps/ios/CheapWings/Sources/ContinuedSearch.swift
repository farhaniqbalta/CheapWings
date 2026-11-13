import BackgroundTasks
import CheapWingsKit
import Foundation
import os

/// iOS 26+ continued processing: a search the user starts keeps running after they leave the
/// app, with progress in system UI. Only ever submitted from a Search/Resume tap (`.fail`, so
/// it never queues to start later). If registration or submission fails, the search stays
/// foreground-first — submitting without a registered handler is a fatal assertion in iOS, so
/// `submit` refuses unless `register()` succeeded.
@available(iOS 26.0, *)
@MainActor
enum ContinuedSearch {
    static let identifierPrefix = "dev.cheapwings.app.search"
    private static let log = Logger(subsystem: "dev.cheapwings.app", category: "ContinuedSearch")

    /// Whether iOS accepted our handler registration.
    private(set) static var isRegistered = false
    /// Set by the model; receives each started continued-processing task.
    static var onTask: ((BGContinuedProcessingTask) -> Void)?

    /// Call once from `application(_:didFinishLaunchingWithOptions:)`.
    static func register() {
        guard !isRegistered else { return }  // a second registration kills the app
        isRegistered = BGTaskScheduler.shared.register(forTaskWithIdentifier: "\(identifierPrefix).*", using: .main) { task in
            MainActor.assumeIsolated {
                guard let task = task as? BGContinuedProcessingTask, let onTask else {
                    task.setTaskCompleted(success: false)
                    return
                }
                onTask(task)
            }
        }
        // Observed false on iPad iOS 27.0.1 with free Personal Team signing (P5.3); searches then
        // stay foreground-first. Open item in docs/log/p5.3.md.
        log.notice("continued-processing handler registered: \(isRegistered, privacy: .public)")
    }

    /// True when the system accepted the request (it then calls the registered handler).
    static func submit(title: String, subtitle: String) -> Bool {
        guard isRegistered else {
            log.notice("continued processing skipped: handler not registered")
            return false
        }
        let request = BGContinuedProcessingTaskRequest(identifier: "\(identifierPrefix).\(UUID().uuidString)",
                                                       title: title, subtitle: subtitle)
        request.strategy = .fail
        do {
            try BGTaskScheduler.shared.submit(request)
            log.notice("continued processing submitted")
            return true
        } catch {
            log.notice("continued processing declined: \(String(describing: error), privacy: .public)")
            return false
        }
    }
}
