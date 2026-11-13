// swift-tools-version:5.9
import PackageDescription

// P5.06 spike S5 (C): the same money + fingerprint + ranking core in plain Swift.
let package = Package(
    name: "SwiftCore",
    platforms: [.iOS(.v17), .macOS(.v13)],
    products: [.library(name: "SwiftCore", targets: ["SwiftCore"])],
    targets: [
        .target(name: "SwiftCore"),
        .executableTarget(name: "swift-core-check", dependencies: ["SwiftCore"]),
    ]
)
