import RustCore
import SwiftUI

@main
struct SizeApp: App {
    // Call the core so the linker keeps it.
    var body: some Scene { WindowGroup { Text("rust \(s5RustRunFixtures(json: "{}").failures.count)") } }
}
