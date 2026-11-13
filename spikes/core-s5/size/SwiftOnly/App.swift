import SwiftCore
import SwiftUI

@main
struct SizeApp: App {
    // Call the core so the linker keeps it.
    var body: some Scene { WindowGroup { Text("swift \(SwiftCore.runFixtures(Data()).failures.count)") } }
}
