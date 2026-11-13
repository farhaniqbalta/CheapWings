import Foundation

/// Port of fli 881aee5 (MIT, Punit Arani) `_proto.encode_tfs_segment` + `encode_tfs_payload`
/// for the only query CheapWings sends: one-way, one adult, economy, any stops.
public enum Tfs {
    public static func encode(origin: String, destination: String, date: String) -> String {
        // Field order matters for byte equality with fli: date, origin (13), destination (14).
        var segment = lengthDelimited(2, Array(date.utf8))
        segment += lengthDelimited(13, varintField(1, 1) + lengthDelimited(2, Array(origin.utf8)))
        segment += lengthDelimited(14, varintField(1, 1) + lengthDelimited(2, Array(destination.utf8)))
        var payload = varintField(1, 28) + varintField(2, 2) + lengthDelimited(3, segment)
        payload += varintField(8, 1)   // one adult
        payload += varintField(9, 1)   // economy
        payload += varintField(14, 1)
        payload += varintField(19, 2)  // one-way
        return Data(payload).base64EncodedString()
            .replacingOccurrences(of: "+", with: "-")
            .replacingOccurrences(of: "/", with: "_")
            .replacingOccurrences(of: "=", with: "")
    }

    /// Same as fli `_tfs.page_url` with CheapWings' `hl=en`.
    public static func pageURL(origin: String, destination: String, date: String,
                               currency: String, country: String) -> URL {
        let tfs = encode(origin: origin, destination: destination, date: date)
        return URL(string: "https://www.google.com/travel/flights?tfs=\(tfs)&hl=en&gl=\(country)&curr=\(currency)")!
    }

    static func varint(_ value: UInt64) -> [UInt8] {
        var value = value
        var out: [UInt8] = []
        repeat {
            var byte = UInt8(value & 0x7F)
            value >>= 7
            if value != 0 { byte |= 0x80 }
            out.append(byte)
        } while value != 0
        return out
    }

    static func varintField(_ field: UInt64, _ value: UInt64) -> [UInt8] {
        varint(field << 3) + varint(value)
    }

    static func lengthDelimited(_ field: UInt64, _ bytes: [UInt8]) -> [UInt8] {
        varint(field << 3 | 2) + varint(UInt64(bytes.count)) + bytes
    }
}
