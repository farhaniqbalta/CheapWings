// swift-tools-version:5.9
import PackageDescription

// Native iPad pieces over the shared Rust core: URLSession Fli transport, paced search engine,
// price display. Business rules stay in CheapWingsCore (Rust).
let package = Package(
    name: "CheapWingsKit",
    platforms: [.iOS(.v17), .macOS(.v13)],
    products: [.library(name: "CheapWingsKit", targets: ["CheapWingsKit"])],
    dependencies: [.package(path: "../CheapWingsCore")],
    targets: [
        .target(name: "CheapWingsKit", dependencies: [.product(name: "CheapWingsCore", package: "CheapWingsCore")]),
        .testTarget(name: "CheapWingsKitTests", dependencies: ["CheapWingsKit"]),
    ]
)
