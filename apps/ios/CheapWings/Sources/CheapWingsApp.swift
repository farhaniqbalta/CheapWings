import SwiftUI

@main
struct CheapWingsApp: App {
    @State private var model = SearchModel()

    var body: some Scene {
        WindowGroup {
            NavigationSplitView {
                SearchView(model: model)
            } detail: {
                ResultsView(model: model)
            }
        }
    }
}
