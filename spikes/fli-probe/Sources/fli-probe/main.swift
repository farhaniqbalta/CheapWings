import FliProbe
import Foundation

// fli-probe selftest
// fli-probe fetch --live ORIGIN DEST YYYY-MM-DD CURRENCY COUNTRY [system|safariIOS|chromeDesktop]
let args = Array(CommandLine.arguments.dropFirst())

switch args.first {
case "selftest":
    let failures = SelfTest.run()
    failures.forEach { print("FAIL \($0)") }
    print(failures.isEmpty ? "selftest OK" : "selftest FAILED (\(failures.count))")
    exit(failures.isEmpty ? 0 : 1)
case "fetch" where args.count >= 7 && args[1] == "--live":
    // One live request to Google Flights; needs owner approval (WORK_LOG: confirm before live probes).
    let ua = args.count > 7 ? UserAgentMode(rawValue: args[7]) : .safariIOS
    guard let ua else { print("unknown UA mode"); exit(2) }
    let result = await FliProbe.run(origin: args[2], destination: args[3], date: args[4],
                                    currency: args[5], country: args[6], userAgent: ua)
    print(result.summary)
    if let offer = result.firstOffer { print("first: \(offer)") }
    if result.outcome.mustStop { print("STOP: no further live requests today (P5.05 §7).") }
    exit(result.outcome == .pass ? 0 : 1)
default:
    print("""
    usage: fli-probe selftest
           fli-probe fetch --live ORIGIN DEST YYYY-MM-DD CURRENCY COUNTRY [system|safariIOS|chromeDesktop]
    """)
    exit(2)
}
