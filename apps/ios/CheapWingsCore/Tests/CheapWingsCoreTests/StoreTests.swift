import CheapWingsCore
import XCTest

final class StoreTests: XCTestCase {
    func testRoundTripThroughFFI() throws {
        let dir = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        try FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
        defer { try? FileManager.default.removeItem(at: dir) }
        let path = dir.appendingPathComponent("searches.sqlite").path

        let request = StoredRequest(origins: ["CGK"], destinations: ["DPS"], dateFrom: "2026-12-15",
                                    dateThrough: "2026-12-16", currency: "IDR")
        let combos = try planSearch(origins: ["CGK"], destinations: ["DPS"], dateFrom: "2026-12-15",
                                    dateThrough: "2026-12-16", maxCombinations: 120)
        let leg = FliLeg(origin: "CGK", destination: "DPS", airline: "GA", flightNumber: "402",
                         departLocal: "2026-12-15T06:05", arriveLocal: "2026-12-15T09:00")
        let id: Int64
        do {
            let store = try SearchStore(path: path)
            id = try store.createSearch(request: request, combos: combos, nowMs: 1_000)
            try store.finishCombo(searchId: id, index: 0, offers: [FliOffer(price: "1234.50", currency: "IDR", legs: [leg])],
                                  hidden: ["currency None"], failure: nil, nowMs: 2_000)
        }
        let reopened = try SearchStore(path: path)
        let latest = try XCTUnwrap(reopened.latest())
        XCTAssertEqual(latest.id, id)
        XCTAssertEqual(latest.request, request)
        XCTAssertEqual(latest.offers.map(\.offer.price), ["1234.50"])
        XCTAssertEqual(latest.hidden, [HiddenCount(reason: "currency None", count: 1)])
        XCTAssertEqual(try reopened.pending(searchId: id).map(\.routeDate.date), ["2026-12-16"])
    }

    func testCorruptFileThrowsInsteadOfCrashing() throws {
        let path = FileManager.default.temporaryDirectory.appendingPathComponent("\(UUID().uuidString).sqlite").path
        try Data("not a database at all, definitely not sqlite".utf8).write(to: URL(fileURLWithPath: path))
        defer { try? FileManager.default.removeItem(atPath: path) }
        XCTAssertThrowsError(try SearchStore(path: path)) { error in
            guard case StoreError.Failed(let code, _) = error else { return XCTFail("\(error)") }
            XCTAssertEqual(code, "open")
        }
    }
}
