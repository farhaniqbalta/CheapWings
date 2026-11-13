@testable import CheapWingsKit
import XCTest

final class PriceTextTests: XCTestCase {
    func testGroupsDigitsWithoutLosingTheFraction() {
        XCTAssertEqual(PriceText.display("1250000", currency: "IDR"), "IDR 1,250,000")
        XCTAssertEqual(PriceText.display("1234.50", currency: "USD"), "USD 1,234.50")
        XCTAssertEqual(PriceText.display("75", currency: "USD"), "USD 75")
        XCTAssertEqual(PriceText.display("999", currency: "IDR"), "IDR 999")
    }

    func testCountryFollowsCurrency() {
        let request = { (c: String) in SearchRequest(origins: ["CGK"], destinations: ["DPS"], dateFrom: "2026-12-15", dateThrough: "2026-12-15", currency: c) }
        XCTAssertEqual(["IDR", "USD", "AUD", "JPY"].map { request($0).country }, ["ID", "US", "AU", "JP"])
    }
}
