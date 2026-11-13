// swift-tools-version:5.9
import PackageDescription

// P5.06 spike S1/S3: can native URLSession get Google Flights `ds:1` rows?
let package = Package(
    name: "FliProbe",
    platforms: [.iOS(.v17), .macOS(.v13)],
    products: [.library(name: "FliProbe", targets: ["FliProbe"])],
    targets: [
        .target(name: "FliProbe"),
        .executableTarget(name: "fli-probe", dependencies: ["FliProbe"]),
    ]
)
