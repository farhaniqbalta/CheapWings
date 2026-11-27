import CheapWingsCore
import Foundation

/// Turns a typed budget ("1.500.000", "Rp 1 500 000", "250,50") into the plain decimal the Rust core
/// validates. Text without digits is returned as typed so the core reports why it is invalid.
public enum BudgetText {
    public static func normalize(_ text: String, currency: String) -> String? {
        let trimmed = text.trimmingCharacters(in: .whitespaces)
        if trimmed.isEmpty { return nil }
        let kept = trimmed.filter { $0.isASCII && ($0.isNumber || $0 == "." || $0 == ",") }
        guard kept.contains(where: \.isNumber) else { return trimmed }
        // Currencies without minor units (IDR, JPY): every separator is grouping.
        if (try? minorUnitExponent(currency: currency)) == 0 { return kept.filter(\.isNumber) }
        guard let last = kept.lastIndex(where: { $0 == "." || $0 == "," }) else { return kept }
        let decimals = kept[kept.index(after: last)...]
        // A last separator followed by 1–2 digits is the decimal point; anything else is grouping.
        guard (1...2).contains(decimals.count) else { return kept.filter(\.isNumber) }
        return kept[..<last].filter(\.isNumber) + "." + decimals
    }
}
