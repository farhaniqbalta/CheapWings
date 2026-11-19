// swift-tools-version:5.9
import PackageDescription
import Foundation

let packageRoot = URL(fileURLWithPath: #filePath).deletingLastPathComponent()
let source = packageRoot.appendingPathComponent("Sources/CheapWingsCore/Generated.swift")
let header = packageRoot.appendingPathComponent(
    "cheapwings_ffiFFI.xcframework/macos-arm64/Headers/cheapwings_ffiFFI/cheapwings_ffiFFI.h"
)
guard let ffiHeader = try? String(contentsOf: header, encoding: .utf8),
      ffiHeader.contains("cheapwings_core_build_revision"),
      let generated = try? String(contentsOf: source, encoding: .utf8),
      generated.contains("    verifyCoreRevision()") else {
    fatalError("Missing or stale CheapWingsCore bindings. Run core/build-ios.sh.")
}

// CheapWings shared Rust core for the iPad app. Run core/build-ios.sh first: it builds the
// XCFramework and generates Sources/CheapWingsCore/Generated.swift (both gitignored).
let package = Package(
    name: "CheapWingsCore",
    platforms: [.iOS(.v17), .macOS(.v13)],
    products: [.library(name: "CheapWingsCore", targets: ["CheapWingsCore"])],
    targets: [
        .binaryTarget(name: "cheapwings_ffiFFI", path: "cheapwings_ffiFFI.xcframework"),
        .target(name: "CheapWingsCore", dependencies: ["cheapwings_ffiFFI"],
                linkerSettings: [.linkedLibrary("sqlite3")]),  // on-device search store (OS SQLite)
        .testTarget(name: "CheapWingsCoreTests", dependencies: ["CheapWingsCore"]),
    ]
)
