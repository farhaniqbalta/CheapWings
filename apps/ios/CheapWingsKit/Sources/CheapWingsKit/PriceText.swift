/// Price display straight from the exact decimal text — never via Double.
public enum PriceText {
    /// `"1250000", "IDR"` → `"IDR 1,250,000"`; `"1234.50", "USD"` → `"USD 1,234.50"`.
    public static func display(_ price: String, currency: String) -> String {
        let negative = price.hasPrefix("-")
        let unsigned = negative ? String(price.dropFirst()) : price
        let parts = unsigned.split(separator: ".", maxSplits: 1, omittingEmptySubsequences: false)
        var grouped = ""
        for (i, digit) in parts[0].reversed().enumerated() {
            if i > 0 && i % 3 == 0 { grouped.insert(",", at: grouped.startIndex) }
            grouped.insert(digit, at: grouped.startIndex)
        }
        let fraction = parts.count > 1 ? "." + parts[1] : ""
        return "\(currency) \(negative ? "-" : "")\(grouped)\(fraction)"
    }
}
