import SwiftUI
import UIKit

/// Background-task handlers must be registered during launch (iOS asserts on submitting an
/// identifier without one), so registration lives here rather than in a SwiftUI initializer.
final class AppDelegate: NSObject, UIApplicationDelegate {
    func application(_ application: UIApplication,
                     didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]? = nil) -> Bool {
        if #available(iOS 26.0, *) { MainActor.assumeIsolated { ContinuedSearch.register() } }
        return true
    }
}

@main
struct CheapWingsApp: App {
    @UIApplicationDelegateAdaptor(AppDelegate.self) private var appDelegate
    @State private var model = SearchModel()
    /// On iPhone and narrow iPad windows the split view collapses; show results once a search starts.
    @State private var compactColumn = NavigationSplitViewColumn.sidebar

    var body: some Scene {
        WindowGroup {
            NavigationSplitView(preferredCompactColumn: $compactColumn) {
                SearchView(model: model)
            } detail: {
                // Own stack so opening a flight pushes details with a Back button.
                NavigationStack { ResultsView(model: model) }
            }
            .onChange(of: model.session.isRunning) { _, running in
                if running { compactColumn = .detail }
            }
        }
    }
}
