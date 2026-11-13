// swift-tools-version:5.9
import PackageDescription

// P5.06 spike S2: Swift wrapper around the Rust wreq library (run ../build.sh first).
let package = Package(
    name: "FliWreq",
    platforms: [.iOS(.v17), .macOS(.v13)],
    products: [.library(name: "FliWreq", targets: ["FliWreq"])],
    dependencies: [.package(path: "../../fli-probe")],
    targets: [
        .binaryTarget(name: "fli_wreqFFI", path: "fli_wreqFFI.xcframework"),
        .target(
            name: "FliWreq",
            dependencies: ["fli_wreqFFI", .product(name: "FliProbe", package: "fli-probe")],
            linkerSettings: [.linkedLibrary("c++")]  // BoringSSL
        ),
        // Offline link check: builds the Chrome-emulating client, sends nothing.
        .executableTarget(name: "wreq-check", dependencies: ["FliWreq"]),
    ]
)
