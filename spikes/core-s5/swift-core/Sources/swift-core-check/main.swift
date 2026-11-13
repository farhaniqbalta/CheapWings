import Foundation
import SwiftCore

// swift-core-check path/to/fixtures.json [rounds]
let args = CommandLine.arguments
guard args.count > 1, let json = FileManager.default.contents(atPath: args[1]) else {
    print("usage: swift-core-check fixtures.json [rounds]")
    exit(2)
}
let report = SwiftCore.runFixtures(json)
report.failures.prefix(10).forEach { print("FAIL \($0)") }
print("Swift core: \(report.checked) cases, \(report.failures.count) failures")
if args.count > 2, let rounds = Int(args[2]) {
    print(String(format: "Swift bench: %d rounds in %.3f s", rounds, SwiftCore.bench(json, rounds: rounds)))
}
exit(report.failures.isEmpty ? 0 : 1)
