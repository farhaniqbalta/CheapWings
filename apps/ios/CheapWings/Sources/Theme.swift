import CheapWingsCore
import CheapWingsKit
import SwiftUI
import UIKit

/// P5.6 design tokens (owner-approved mockup). Yellow only marks "cheapest" or the main action;
/// everything else uses system colours so dark mode and Increase Contrast work unchanged.
enum Theme {
    /// Taxiway-sign yellow; text on it is always `onSign`.
    static let sign = Color(red: 0xF5 / 255, green: 0xC4 / 255, blue: 0x00 / 255)
    static let onSign = Color.black
    /// Google stop states (rate-limited / blocked).
    static let hold = Color(red: 0xD7 / 255, green: 0x26 / 255, blue: 0x2E / 255)
    /// Warning text (airport change, stale price): system orange is too light on white.
    static let warn = Color(UIColor { $0.userInterfaceStyle == .dark
        ? UIColor(red: 1, green: 0x9F / 255, blue: 0x0A / 255, alpha: 1)
        : UIColor(red: 0xA6 / 255, green: 0x4B / 255, blue: 0, alpha: 1) })
}

extension View {
    /// IATA codes and the route header: wide letterforms, like airport signs; scales with Dynamic Type.
    func codeStyle(_ style: Font.TextStyle = .body) -> some View {
        font(.system(style, weight: .bold)).fontWidth(.expanded)
    }
}

/// An airline's two-letter designator as a small outlined plate, in the same wide sign letters as
/// airport codes. No logos (none available, and imitations would mislead) and no airline colours
/// (yellow stays reserved for "cheapest" and the main action).
struct CarrierPlate: View {
    let code: String

    var body: some View {
        Text(code)
            .font(.caption.weight(.bold)).fontWidth(.expanded)
            .padding(.horizontal, 5).padding(.vertical, 2)
            .overlay(RoundedRectangle(cornerRadius: 5).strokeBorder(.secondary, lineWidth: 1))
            .accessibilityHidden(true)  // the airline name is read instead
    }
}

/// Plates + "Garuda Indonesia and Korean Air" on one line; wraps under the plates when narrow.
struct CarriersLine: View {
    let carriers: [AirlineNames.Carrier]
    var font: Font = .subheadline.weight(.medium)

    var body: some View {
        HStack(alignment: .firstTextBaseline, spacing: 6) {
            HStack(spacing: 4) { ForEach(carriers, id: \.code) { CarrierPlate(code: $0.code) } }
                .alignmentGuide(.firstTextBaseline) { $0[.bottom] - 4 }
            let names = carriers.compactMap(\.name)
            if !names.isEmpty { Text(names.joined(separator: " and ")).font(font) }
        }
    }
}

/// Search sources the iPad can use (P5.4). Order is the display order.
enum Sources {
    static let all = ["fli", "skiplagged"]

    static func name(_ id: String) -> String {
        switch id {
        case "fli": return "Google Flights"
        case "skiplagged": return "Skiplagged"
        default: return id
        }
    }

    /// Short label for result rows.
    static func short(_ id: String) -> String { id == "fli" ? "Google" : name(id) }
}

/// Which source a fare came from: an outlined label, quiet like the carrier plate, never yellow.
struct SourcePlate: View {
    let provider: String

    var body: some View {
        Text(Sources.short(provider))
            .font(.caption2.weight(.semibold))
            .padding(.horizontal, 6).padding(.vertical, 2)
            .foregroundStyle(.secondary)
            .overlay(RoundedRectangle(cornerRadius: 5).strokeBorder(.tertiary, lineWidth: 1))
            .accessibilityLabel("From \(Sources.name(provider))")
    }
}

enum FxText {
    /// "Converted from US$271 at 18,108.7 (rate of 9 Nov)", "Not converted: Skiplagged sent no IDR rate", or nil.
    static func note(_ offer: SourceOffer, displayCurrency: String) -> String? {
        guard offer.currencyOriginal != displayCurrency else { return nil }
        let original = PriceText.display(offer.priceOriginal, currency: offer.currencyOriginal)
        guard let fx = offer.fx else {
            return offer.priceComparable == nil
                ? "Not converted: \(Sources.name(offer.provider)) sent no \(displayCurrency) rate"
                : nil
        }
        let day = ISO8601DateFormatter().date(from: fx.asOf).map { $0.formatted(.dateTime.day().month(.abbreviated)) }
        return "Converted from \(original) at \(fx.rate)" + (day.map { " (rate of \($0))" } ?? "")
    }
}

/// Short fare for the date strip: "1.25M", "312", "48k" (display only; exact price is elsewhere).
enum CompactPrice {
    static func text(_ price: String) -> String {
        guard let value = Decimal(string: price) else { return price }
        func rounded(_ v: Decimal, _ scale: Int) -> String {
            var input = v, output = Decimal()
            NSDecimalRound(&output, &input, scale, .plain)
            return NSDecimalNumber(decimal: output).stringValue
        }
        if value >= 1_000_000 { return rounded(value / 1_000_000, 2) + "M" }
        if value >= 10_000 { return rounded(value / 1_000, 0) + "k" }
        return rounded(value, 0)
    }
}
