import CryptoKit
import Foundation

/// S5 (C): Swift port of money.py arithmetic, compute_fingerprint and ranking.py.
public enum SwiftCore {
    // MARK: money

    static let exponents: [String: Int] = [
        "IDR": 0, "JPY": 0, "KRW": 0, "VND": 0,
        "USD": 2, "AUD": 2, "EUR": 2, "GBP": 2, "CAD": 2, "SGD": 2, "MYR": 2, "INR": 2, "CNY": 2,
        "HKD": 2, "NZD": 2, "CHF": 2, "THB": 2, "PHP": 2, "BRL": 2, "MXN": 2, "CZK": 2, "DKK": 2,
        "SEK": 2, "PLN": 2, "RON": 2, "TRY": 2, "TWD": 2, "UAH": 2,
    ]
    private static let posix = Locale(identifier: "en_US_POSIX")

    static func parse(_ text: String) -> Decimal? { Decimal(string: text, locale: posix) }

    static func pow10(_ n: Int) -> Decimal { Decimal(sign: .plus, exponent: n, significand: 1) }

    /// Integer digits with a decimal point `scale` places from the right ("-5", 2 → "-0.05").
    static func withPoint(_ integer: String, scale: Int, negativeZero: Bool = false) -> String {
        var digits = integer
        let negative = digits.hasPrefix("-") || negativeZero
        if digits.hasPrefix("-") { digits.removeFirst() }
        if scale > 0 {
            digits = String(repeating: "0", count: max(0, scale + 1 - digits.count)) + digits
            digits.insert(".", at: digits.index(digits.endIndex, offsetBy: -scale))
        }
        return (negative ? "-" : "") + digits
    }

    /// Integral Decimal → plain integer text (no exponent notation).
    static func integerText(_ value: Decimal) -> String { NSDecimalNumber(decimal: value).stringValue }

    static func isIntegral(_ value: Decimal) -> Bool {
        var input = value, rounded = Decimal()
        NSDecimalRound(&rounded, &input, 0, .plain)
        return rounded == value
    }

    public static func fxConvert(amount: String, rate: String, currency: String) -> String? {
        guard let exp = exponents[currency.uppercased()], let a = parse(amount), let r = parse(rate) else { return nil }
        var product = a * r, rounded = Decimal()
        NSDecimalRound(&rounded, &product, exp, .bankers)
        // Python keeps the sign when a negative product rounds to zero ("-0.00"); Decimal has no -0.
        return withPoint(integerText(rounded * pow10(exp)), scale: exp, negativeZero: product < 0 && rounded == 0)
    }

    public static func fromMinorUnits(_ minor: Int, currency: String) -> String? {
        guard let exp = exponents[currency.uppercased()] else { return nil }
        return withPoint(String(minor), scale: exp)
    }

    public static func asMinorUnits(amount: String, currency: String) -> String? {
        guard let exp = exponents[currency.uppercased()], let a = parse(amount) else { return nil }
        let scaled = a * pow10(exp)
        return isIntegral(scaled) ? integerText(scaled) : nil
    }

    // MARK: fingerprint

    public struct Instant: Decodable {
        let y, mo, d, h, mi, s, us, offset: Int
    }

    public struct Segment: Decodable {
        let ordinal: Int
        let marketing, operating, flight, origin, destination: String
        let depart, arrive: Instant
    }

    /// Byte-identical to Python `datetime.isoformat()` for an aware datetime.
    static func isoformat(_ t: Instant) -> String {
        var out = String(format: "%04d-%02d-%02dT%02d:%02d:%02d", t.y, t.mo, t.d, t.h, t.mi, t.s)
        if t.us != 0 { out += String(format: ".%06d", t.us) }
        let off = abs(t.offset)
        out += String(format: "%@%02d:%02d", t.offset < 0 ? "-" : "+", off / 3600, off % 3600 / 60)
        if off % 60 != 0 { out += String(format: ":%02d", off % 60) }
        return out
    }

    public static func fingerprint(_ segments: [Segment]) -> String {
        let canonical = segments.map {
            [String($0.ordinal), $0.marketing, $0.operating, $0.flight, $0.origin, $0.destination,
             isoformat($0.depart), isoformat($0.arrive)].joined(separator: ",")
        }.joined(separator: "|")
        return SHA256.hash(data: Data(canonical.utf8)).map { String(format: "%02x", $0) }.joined()
    }

    // MARK: ranking

    public struct Offer: Decodable {
        let id: String
        let price_status, hidden_city, comparison_status: String
        let amount: String?
    }

    static func tier(_ status: String) -> Int {
        ["repriced_exact": 0, "recent_search": 1, "indicative": 2][status] ?? 3
    }

    /// `best_checked_deal`; the index tie-break reproduces Python's stable sort.
    public static func bestCheckedDeal(_ groups: [[Offer]]) -> [String] {
        groups.joined().enumerated()
            .filter { $0.element.hidden_city == "no" && $0.element.comparison_status == "eligible_total_known" }
            .compactMap { item in item.element.amount.flatMap(parse).map { (item.offset, tier(item.element.price_status), $0, item.element.id) } }
            .sorted { ($0.1, $0.2, $0.0) < ($1.1, $1.2, $1.0) }
            .map(\.3)
    }

    public static func lowestAdvertised(_ groups: [[Offer]]) -> [String] {
        groups.joined().enumerated()
            .filter { $0.element.hidden_city != "yes" }
            .compactMap { item in item.element.amount.flatMap(parse).map { (item.offset, $0, item.element.id) } }
            .sorted { ($0.1, $0.0) < ($1.1, $1.0) }
            .map(\.2)
    }

    // MARK: fixtures + bench

    struct MoneyCase: Decodable { let op: String; let amount, rate, minor: String?; let currency: String; let expect: String? }
    struct FingerprintCase: Decodable { let segments: [Segment]; let expect: String }
    struct RankingCase: Decodable { let groups: [[Offer]]; let best, lowest: [String] }
    struct Fixtures: Decodable { let money: [MoneyCase]; let fingerprint: [FingerprintCase]; let ranking: [RankingCase] }

    static func moneyResult(_ c: MoneyCase) -> String? {
        switch c.op {
        case "fx": return c.amount.flatMap { a in c.rate.flatMap { fxConvert(amount: a, rate: $0, currency: c.currency) } }
        case "from_minor": return c.minor.flatMap(Int.init).flatMap { fromMinorUnits($0, currency: c.currency) }
        default: return c.amount.flatMap { asMinorUnits(amount: $0, currency: c.currency) }
        }
    }

    public static func runFixtures(_ json: Data) -> (checked: Int, failures: [String]) {
        guard let f = try? JSONDecoder().decode(Fixtures.self, from: json) else { return (0, ["fixture parse failed"]) }
        var failures: [String] = []
        for c in f.money where moneyResult(c) != c.expect {
            failures.append("money \(c.op) \(c.amount ?? c.minor ?? "") \(c.currency): got \(moneyResult(c) ?? "nil") want \(c.expect ?? "nil")")
        }
        for (i, c) in f.fingerprint.enumerated() where fingerprint(c.segments) != c.expect { failures.append("fingerprint #\(i)") }
        for (i, c) in f.ranking.enumerated() where bestCheckedDeal(c.groups) != c.best || lowestAdvertised(c.groups) != c.lowest {
            failures.append("ranking #\(i)")
        }
        return (f.money.count + f.fingerprint.count + f.ranking.count, failures)
    }

    /// Seconds spent running every fixture case `rounds` times (JSON decoding excluded).
    public static func bench(_ json: Data, rounds: Int) -> Double {
        guard let f = try? JSONDecoder().decode(Fixtures.self, from: json) else { return -1 }
        var sink = 0
        let elapsed = ContinuousClock().measure {
            for _ in 0..<rounds {
                for c in f.money { sink += moneyResult(c)?.count ?? 0 }
                for c in f.fingerprint { sink += fingerprint(c.segments).count }
                for c in f.ranking { sink += bestCheckedDeal(c.groups).count + lowestAdvertised(c.groups).count }
            }
        }
        withExtendedLifetime(sink) {}
        return Double(elapsed.components.seconds) + Double(elapsed.components.attoseconds) / 1e18
    }
}
