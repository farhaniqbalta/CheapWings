import FliProbe
import FliWreq
import SwiftUI

@main
struct FliProbeApp: App {
    var body: some Scene { WindowGroup { ProbeView() } }
}

enum Transport: String, CaseIterable {
    case urlSession = "URLSession (S1)"
    case wreq = "Rust wreq Chrome (S2)"
}

struct ProbeView: View {
    @State private var origin = "CGK"
    @State private var destination = "DPS"
    @State private var date = Calendar.current.date(byAdding: .day, value: 30, to: .now)!
    @State private var currency = "IDR"
    @State private var country = "ID"
    @State private var transport = Transport.urlSession
    @State private var userAgent = UserAgentMode.safariIPad
    @State private var results: [ProbeResult] = []
    @State private var running = false
    @State private var stopped = false          // latched after any block / 429 (P5.05 §7)
    @State private var lastRun = Date.distantPast
    @State private var message = ""

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
                    Picker("Transport", selection: $transport) {
                        ForEach(Transport.allCases, id: \.self) { Text($0.rawValue) }
                    }
                    if transport == .urlSession {
                        Picker("User-Agent", selection: $userAgent) {
                            ForEach(UserAgentMode.allCases, id: \.self) { Text($0.rawValue) }
                        }
                    }
                }
                Section("Offline checks (no network)") {
                    Button("Decoder self-test") {
                        let failures = SelfTest.run()
                        message = failures.isEmpty ? "selftest OK" : failures.joined(separator: "\n")
                    }
                    Button("wreq Chrome client builds on this device?") {
                        message = WreqProbe.clientBuildError().map { "wreq client FAILED: \($0)" } ?? "wreq client OK"
                    }
                    if !message.isEmpty { Text(message).font(.footnote.monospaced()) }
                }
                Section {
                    Button(running ? "Running…" : "Send ONE live request", action: probe)
                        .disabled(running || stopped)
                    if stopped { Text("Stopped: blocked or rate-limited. No more requests today.").foregroundStyle(.red) }
                    Text("Pass = 3 runs, all PASS, ≥10 s apart, same transport.").font(.footnote)
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
            .navigationTitle("Fli probe")
        }
    }

    private func probe() {
        let wait = minGap - Date().timeIntervalSince(lastRun)
        guard wait <= 0 else { message = String(format: "Wait %.0f s between requests.", wait); return }
        let day = date.formatted(.iso8601.year().month().day())
        running = true
        lastRun = .now
        Task {
            let result: ProbeResult
            switch transport {
            case .urlSession:
                result = await FliProbe.run(origin: origin, destination: destination, date: day,
                                            currency: currency, country: country, userAgent: userAgent)
            case .wreq:
                result = await WreqProbe.run(origin: origin, destination: destination, date: day,
                                             currency: currency, country: country)
            }
            results.insert(result, at: 0)
            stopped = stopped || result.outcome.mustStop
            running = false
        }
    }
}
