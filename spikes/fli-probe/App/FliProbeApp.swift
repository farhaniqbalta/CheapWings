import FliProbe
import SwiftUI

// Drop-in app file for an Xcode "iOS App" project that adds this package (see README).
@main
struct FliProbeApp: App {
    var body: some Scene { WindowGroup { ProbeView() } }
}

struct ProbeView: View {
    @State private var origin = "CGK"
    @State private var destination = "DPS"
    @State private var date = Calendar.current.date(byAdding: .day, value: 30, to: .now)!
    @State private var currency = "IDR"
    @State private var country = "ID"
    @State private var userAgent = UserAgentMode.safariIOS
    @State private var results: [ProbeResult] = []
    @State private var running = false
    @State private var stopped = false          // latched after any block / 429 (P5.05 §7)
    @State private var lastRun = Date.distantPast
    @State private var selfTest = ""

    private let minGap: TimeInterval = 10      // stricter than Fli's 1 s production interval

    var body: some View {
        NavigationStack {
            Form {
                Section("Query") {
                    TextField("Origin", text: $origin).textInputAutocapitalization(.characters)
                    TextField("Destination", text: $destination).textInputAutocapitalization(.characters)
                    DatePicker("Date", selection: $date, displayedComponents: .date)
                    TextField("Currency", text: $currency).textInputAutocapitalization(.characters)
                    TextField("Country (gl)", text: $country).textInputAutocapitalization(.characters)
                    Picker("User-Agent", selection: $userAgent) {
                        ForEach(UserAgentMode.allCases, id: \.self) { Text($0.rawValue) }
                    }
                }
                Section {
                    Button("Run offline self-test") {
                        let failures = SelfTest.run()
                        selfTest = failures.isEmpty ? "selftest OK" : failures.joined(separator: "\n")
                    }
                    if !selfTest.isEmpty { Text(selfTest).font(.footnote.monospaced()) }
                    Button(running ? "Running…" : "Send ONE live request", action: probe)
                        .disabled(running || stopped)
                    if stopped { Text("Stopped: blocked or rate-limited. No more requests today.").foregroundStyle(.red) }
                    Text("Pass = 3 runs, all PASS, ≥10 s apart.").font(.footnote)
                }
                Section("Results (\(results.filter { $0.outcome == .pass }.count) pass / \(results.count))") {
                    ForEach(Array(results.enumerated()), id: \.offset) { _, r in
                        VStack(alignment: .leading, spacing: 4) {
                            Text(r.summary).font(.caption.monospaced())
                            if let first = r.firstOffer { Text(first).font(.caption) }
                            Link("Open search on Google Flights", destination: r.searchURL).font(.caption)
                        }
                    }
                    if !results.isEmpty {
                        ShareLink("Share summaries", item: results.map(\.summary).joined(separator: "\n"))
                    }
                }
            }
            .navigationTitle("Fli probe (S1)")
        }
    }

    private func probe() {
        let wait = minGap - Date().timeIntervalSince(lastRun)
        guard wait <= 0 else { selfTest = String(format: "Wait %.0f s between requests.", wait); return }
        let day = date.formatted(.iso8601.year().month().day())
        running = true
        lastRun = .now
        Task {
            let result = await FliProbe.run(origin: origin, destination: destination, date: day,
                                            currency: currency, country: country, userAgent: userAgent)
            results.insert(result, at: 0)
            stopped = stopped || result.outcome.mustStop
            running = false
        }
    }
}
