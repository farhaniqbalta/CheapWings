@testable import CheapWingsKit
import XCTest

/// P7.8: the Discover budget accepts how people type money (Indonesian dots, commas, spaces).
final class BudgetTextTests: XCTestCase {
    func testWholeUnitCurrenciesDropGrouping() {
        XCTAssertEqual(BudgetText.normalize("1.500.000", currency: "IDR"), "1500000")
        XCTAssertEqual(BudgetText.normalize("1,500,000", currency: "IDR"), "1500000")
        XCTAssertEqual(BudgetText.normalize(" Rp 1 500 000 ", currency: "IDR"), "1500000")
        XCTAssertEqual(BudgetText.normalize("20.000", currency: "JPY"), "20000")
    }

    func testCentCurrenciesKeepTheDecimal() {
        XCTAssertEqual(BudgetText.normalize("250,50", currency: "USD"), "250.50")
        XCTAssertEqual(BudgetText.normalize("1,250.50", currency: "AUD"), "1250.50")
        XCTAssertEqual(BudgetText.normalize("300", currency: "USD"), "300")
    }

    func testEmptyIsNoBudgetAndJunkIsKept() {
        XCTAssertNil(BudgetText.normalize("  ", currency: "IDR"))
        XCTAssertEqual(BudgetText.normalize("abc", currency: "IDR"), "abc", "the core still rejects it with its reason")
    }
}
