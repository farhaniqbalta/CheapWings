// swift-tools-version:5.9
import PackageDescription

// P5.06 spike S5 (B): Swift wrapper around the Rust core (run ../rust/build.sh first).
let package = Package(
    name: "RustCore",
    platforms: [.iOS(.v17), .macOS(.v13)],
    products: [.library(name: "RustCore", targets: ["RustCore"])],
    targets: [
        .binaryTarget(name: "core_s5FFI", path: "core_s5FFI.xcframework"),
        .target(name: "RustCore", dependencies: ["core_s5FFI"]),
    ]
)
