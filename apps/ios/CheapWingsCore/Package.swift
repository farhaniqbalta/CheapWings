// swift-tools-version:5.9
import PackageDescription

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
