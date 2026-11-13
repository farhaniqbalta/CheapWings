import Foundation

public struct Leg: Sendable {
    public let origin, destination, airline, flightNumber: String
    public let departLocal, arriveLocal: String  // naive local wall time, as Google sends it
}

public struct Offer: Sendable {
    public let price: Decimal
    public let priceText: String
    public let currency: String?
    public let legs: [Leg]
}

public struct Decoded: Sendable {
    public let offers: [Offer]
    public let unpriced: Int
}

public enum DecodeError: Error, CustomStringConvertible {
    case schemaChanged(String)
    case partialPayload

    public var description: String {
        switch self {
        case .schemaChanged(let why): return "schema_changed: \(why)"
        case .partialPayload: return "partial_payload"
        }
    }
}

/// Mirrors `providers/fli.py` `_fetch` extraction + `normalize`, and fli 881aee5 `_decoders`.
public enum Page {
    private static let blob = try! NSRegularExpression(
        pattern: #"AF_initDataCallback\((\{.*?\})\);"#, options: .dotMatchesLineSeparators)
    private static let key = try! NSRegularExpression(pattern: #"key:\s*'([^']+)'"#)
    private static let data = try! NSRegularExpression(
        pattern: #"data:(.*?), sideChannel"#, options: .dotMatchesLineSeparators)

    public static func isTrafficBlock(_ html: String) -> Bool {
        let lower = html.lowercased()
        return lower.contains("our systems have detected unusual traffic")
            || lower.contains("unusual traffic from your computer")
    }

    /// The `ds:1` JSON payload, or nil when the page has none (a row-less page).
    public static func extractDs1(_ html: String) -> Any? {
        let ns = html as NSString
        for match in blob.matches(in: html, range: NSRange(location: 0, length: ns.length)) {
            let body = ns.substring(with: match.range(at: 1))
            let bodyNS = body as NSString
            guard let k = key.firstMatch(in: body, range: NSRange(location: 0, length: bodyNS.length)),
                  bodyNS.substring(with: k.range(at: 1)) == "ds:1",
                  let d = data.firstMatch(in: body, range: NSRange(location: 0, length: bodyNS.length))
            else { continue }
            let json = bodyNS.substring(with: d.range(at: 1))
            return try? JSONSerialization.jsonObject(with: Data(json.utf8), options: .fragmentsAllowed)
        }
        return nil
    }

    public static func decode(_ payload: Any) throws -> Decoded {
        guard let data = payload as? [Any], data.count >= 4 else { throw DecodeError.schemaChanged("payload shape") }
        var rows: [Any] = []
        var sawGroup = false
        for index in [2, 3] {
            if data[index] is NSNull { continue }
            guard let group = data[index] as? [Any], let first = group.first as? [Any] else {
                throw DecodeError.schemaChanged("row group \(index)")
            }
            sawGroup = true
            rows += first
        }
        if rows.count > 500 { throw DecodeError.partialPayload }
        if !sawGroup { throw DecodeError.schemaChanged("no row groups") }

        var offers: [Offer] = []
        var unpriced = 0
        for case let row as [Any] in rows {
            guard row.count > 1, let priceBlock = row[1] as? [Any], let head = priceBlock.first as? [Any],
                  let detail = row[0] as? [Any], detail.count > 2
            else { throw DecodeError.schemaChanged("row shape") }
            if head.isEmpty { unpriced += 1; continue }
            guard let raw = head.last as? NSNumber else { throw DecodeError.schemaChanged("price") }
            let (price, text) = exactDecimal(raw)
            let token = priceBlock.count > 1 ? priceBlock[1] as? String : nil
            let legs = try (detail[2] as? [Any] ?? []).map(leg)
            offers.append(Offer(price: price, priceText: text, currency: token.flatMap(currency(fromToken:)), legs: legs))
        }
        return Decoded(offers: offers, unpriced: unpriced)
    }

    // shortcut: JSONSerialization yields NSNumber, so integral prices are exact but fractional ones use the
    // shortest round-trip text (trailing zeros lost); upgrade to a byte-level lexeme scanner for the real port.
    static func exactDecimal(_ number: NSNumber) -> (Decimal, String) {
        let text = CFNumberIsFloatType(number) ? "\(number.doubleValue)" : number.stringValue
        return (Decimal(string: text) ?? .nan, text)
    }

    static func leg(_ any: Any) throws -> Leg {
        guard let fl = any as? [Any], fl.count > 22,
              let origin = fl[3] as? String, let destination = fl[6] as? String
        else { throw DecodeError.schemaChanged("leg shape") }
        let airline = fl[22] as? [Any] ?? []
        return Leg(
            origin: origin, destination: destination,
            airline: airline.first as? String ?? "",
            flightNumber: airline.count > 1 ? (airline[1] as? String ?? "") : "",
            departLocal: try localTime(fl[20], fl[8]),
            arriveLocal: try localTime(fl[21], fl[10]))
    }

    static func localTime(_ date: Any, _ time: Any) throws -> String {
        func parts(_ a: Any, _ n: Int) -> [Int] {
            let values = (a as? [Any] ?? []).map { ($0 as? NSNumber)?.intValue ?? 0 }
            return values + Array(repeating: 0, count: max(0, n - values.count))
        }
        let d = parts(date, 3), t = parts(time, 2)
        guard d[0] > 0 else { throw DecodeError.schemaChanged("leg date") }
        return String(format: "%04d-%02d-%02dT%02d:%02d", d[0], d[1], d[2], t[0], t[1])
    }

    /// fli `core/currency.py`: base64url protobuf, field 3 → nested field 3 = ISO code.
    public static func currency(fromToken token: String) -> String? {
        var b64 = token.replacingOccurrences(of: "-", with: "+").replacingOccurrences(of: "_", with: "/")
        b64 += String(repeating: "=", count: (4 - b64.count % 4) % 4)
        guard let bytes = Data(base64Encoded: b64).map(Array.init) else { return nil }
        guard let nested = field(3, in: bytes[...]), let code = field(3, in: nested) else { return nil }
        return String(decoding: code, as: UTF8.self).uppercased()
    }

    /// First length-delimited field `number`, skipping others. Nil on malformed input.
    private static func field(_ number: UInt64, in bytes: ArraySlice<UInt8>) -> ArraySlice<UInt8>? {
        var i = bytes.startIndex
        func readVarint() -> UInt64? {
            var result: UInt64 = 0, shift: UInt64 = 0
            while i < bytes.endIndex, shift < 64 {
                let b = bytes[i]; i += 1
                result |= UInt64(b & 0x7F) << shift
                if b & 0x80 == 0 { return result }
                shift += 7
            }
            return nil
        }
        while i < bytes.endIndex {
            guard let tag = readVarint() else { return nil }
            switch tag & 7 {
            case 0: guard readVarint() != nil else { return nil }
            case 1: i += 8
            case 5: i += 4
            case 2:
                guard let len = readVarint(), i + Int(len) <= bytes.endIndex else { return nil }
                let start = i
                i += Int(len)
                if tag >> 3 == number { return bytes[start..<i] }
            default: return nil
            }
        }
        return nil
    }
}
