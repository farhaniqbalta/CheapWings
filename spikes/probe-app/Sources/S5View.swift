import Foundation
import RustCore
import SwiftCore
import SwiftUI

/// S5: run the Rust and Swift cores against the same Python-generated fixtures, then time them.
struct S5Section: View {
    @State private var lines: [String] = []
    @State private var running = false
    private let rounds = 20

    var body: some View {
        Section("S5 — Rust core vs Swift core (offline)") {
            Button(running ? "Running…" : "Run S5 (fixtures + \(rounds)-round bench)", action: run)
                .disabled(running)
            ForEach(lines, id: \.self) { Text($0).font(.caption.monospaced()) }
            if !lines.isEmpty {
                ShareLink("Share S5 results", item: lines.joined(separator: "\n"))
            }
        }
    }

    private func run() {
        guard let url = Bundle.main.url(forResource: "fixtures", withExtension: "json"),
              let data = try? Data(contentsOf: url) else {
            lines = ["fixtures.json missing from app bundle"]
            return
        }
        running = true
        lines = []
        let rounds = rounds
        Task.detached(priority: .userInitiated) {
            let json = String(decoding: data, as: UTF8.self)
            let rust = s5RustRunFixtures(json: json)
            let swift = SwiftCore.runFixtures(data)
            let rustSeconds = s5RustBench(json: json, rounds: UInt32(rounds))
            let swiftSeconds = SwiftCore.bench(data, rounds: rounds)
            var out = [
                "S5 rust  cases=\(rust.checked) failures=\(rust.failures.count)" + String(format: " bench=%.3fs/%d", rustSeconds, rounds),
                "S5 swift cases=\(swift.checked) failures=\(swift.failures.count)" + String(format: " bench=%.3fs/%d", swiftSeconds, rounds),
            ]
            out += rust.failures.prefix(3).map { "rust FAIL \($0)" } + swift.failures.prefix(3).map { "swift FAIL \($0)" }
            await MainActor.run {
                lines = out
                running = false
            }
        }
    }
}
