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
