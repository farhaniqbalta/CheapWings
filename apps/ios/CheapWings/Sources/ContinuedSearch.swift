import BackgroundTasks
import CheapWingsKit
import Foundation

/// iOS 26+ continued processing: a search the user starts keeps running after they leave the
/// app, with progress in system UI. Only ever submitted from a Search/Resume tap (`.fail`, so
/// it never queues to start later). If the system declines, the search stays foreground-first.
@available(iOS 26.0, *)
@MainActor
enum ContinuedSearch {
    static let identifierPrefix = "dev.cheapwings.app.search"

    /// Register once at launch; the wildcard matches each search's unique identifier.
    static func register(model: SearchModel) {
        BGTaskScheduler.shared.register(forTaskWithIdentifier: "\(identifierPrefix).*", using: .main) { task in
            guard let task = task as? BGContinuedProcessingTask else {
                task.setTaskCompleted(success: false)
                return
            }
            MainActor.assumeIsolated { model.attach(task) }
        }
    }

    /// True when the system accepted the request (it then calls the registered handler).
    static func submit(title: String, subtitle: String) -> Bool {
        let request = BGContinuedProcessingTaskRequest(identifier: "\(identifierPrefix).\(UUID().uuidString)",
                                                       title: title, subtitle: subtitle)
        request.strategy = .fail
        do {
            try BGTaskScheduler.shared.submit(request)
            return true
        } catch {
            return false
        }
    }
}
