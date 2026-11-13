import SwiftUI

@main
struct CheapWingsApp: App {
    @State private var model = SearchModel()
    /// On iPhone and narrow iPad windows the split view collapses; show results once a search starts.
    @State private var compactColumn = NavigationSplitViewColumn.sidebar

    var body: some Scene {
        WindowGroup {
            NavigationSplitView(preferredCompactColumn: $compactColumn) {
                SearchView(model: model)
            } detail: {
                ResultsView(session: model.session)
            }
            .onChange(of: model.session.isRunning) { _, running in
                if running { compactColumn = .detail }
            }
        }
    }
}
