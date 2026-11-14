import CheapWingsKit
import SwiftUI

/// The results' one bold element: one column per departure date with that day's lowest fare.
/// The cheapest day is sign yellow; tapping a day filters the list (tap again for all days).
struct DateRibbon: View {
    let days: [DaySummary]
    @Binding var selected: String?
    @Environment(\.dynamicTypeSize) private var typeSize

    var body: some View {
        // Bars share one scale in the display currency only; unconverted days get no bar.
        let maxPrice = days.compactMap { $0.lowestComparable.flatMap { Decimal(string: $0) } }.max() ?? 1
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 6) {
                ForEach(days) { day in
                    DayColumn(day: day, maxPrice: maxPrice, isSelected: selected == day.date) {
                        selected = selected == day.date ? nil : day.date
                    }
                }
            }
            .padding(.vertical, 2)
        }
        .accessibilityElement(children: .contain)
        .accessibilityLabel("Lowest fare per departure day")
    }
}

private struct DayColumn: View {
    let day: DaySummary
    let maxPrice: Decimal
    let isSelected: Bool
    let tap: () -> Void

    private var date: Date? { SearchModel.date(day.date) }

    var body: some View {
        Button(action: tap) {
            VStack(spacing: 6) {
                Text(date?.formatted(.dateTime.weekday(.abbreviated)) ?? "")
                    .font(.caption.weight(.semibold))
                Text(date?.formatted(.dateTime.day()) ?? day.date)
                    .font(.title3.weight(.bold).monospacedDigit())
                bar
                Text(priceText)
                    .font(.caption.weight(.semibold).monospacedDigit())
                    .lineLimit(1)
                    .minimumScaleFactor(0.7)
            }
            .frame(minWidth: 54, minHeight: 112)
            .padding(.horizontal, 4)
            .foregroundStyle(foreground)
            .background(background, in: RoundedRectangle(cornerRadius: 12))
            .overlay {
                if day.state == .pending {
                    RoundedRectangle(cornerRadius: 12).strokeBorder(style: StrokeStyle(lineWidth: 1.5, dash: [4, 3]))
                        .foregroundStyle(.tertiary)
                }
                if isSelected {
                    RoundedRectangle(cornerRadius: 12).strokeBorder(.primary, lineWidth: 2)
                }
            }
        }
        .buttonStyle(.plain)
        .accessibilityLabel(accessibilityText)
        .accessibilityAddTraits(isSelected ? .isSelected : [])
        .accessibilityHint(isSelected ? "Shows all days" : "Shows flights on this day only")
    }

    @ViewBuilder private var bar: some View {
        let height: CGFloat = {
            guard let price = day.lowestComparable.flatMap({ Decimal(string: $0) }), maxPrice > 0 else { return 0 }
            return CGFloat(truncating: NSDecimalNumber(decimal: 30 * price / maxPrice))
        }()
        RoundedRectangle(cornerRadius: 3)
            .fill(day.isCheapest ? AnyShapeStyle(Theme.onSign) : AnyShapeStyle(.quaternary))
            .frame(width: 22, height: max(height, 0))
            .frame(height: 30, alignment: .bottom)
            .accessibilityHidden(true)
    }

    private var priceText: String {
        if let comparable = day.lowestComparable { return CompactPrice.text(comparable) }
        if let lowest = day.lowest, let other = day.unconvertedCurrency { return "\(other) \(CompactPrice.text(lowest.offer.priceOriginal))" }
        switch day.state {
        case .pending: return "···"
        case .failed: return "—"
        case .searched: return "none"
        }
    }

    private var foreground: AnyShapeStyle {
        if day.isCheapest { return AnyShapeStyle(Theme.onSign) }
        return day.lowest == nil ? AnyShapeStyle(.secondary) : AnyShapeStyle(.primary)
    }

    private var background: AnyShapeStyle {
        if day.isCheapest { return AnyShapeStyle(Theme.sign) }
        return day.state == .pending ? AnyShapeStyle(.clear) : AnyShapeStyle(.background)
    }

    private var accessibilityText: String {
        let when = date?.formatted(.dateTime.weekday(.wide).day().month(.wide)) ?? day.date
        if let lowest = day.lowest {
            let price = PriceText.display(lowest.shownPrice.amount, currency: lowest.shownPrice.currency)
            return "\(when), from \(price)" + (day.isCheapest ? ", cheapest day" : "") + (day.state == .pending ? ", still searching" : "")
        }
        switch day.state {
        case .pending: return "\(when), still searching"
        case .failed(let code): return "\(when), could not be searched (\(code))"
        case .searched: return "\(when), no flights found"
        }
    }
}
