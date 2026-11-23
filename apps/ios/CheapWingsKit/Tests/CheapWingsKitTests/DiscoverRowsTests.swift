import CheapWingsCore
@testable import CheapWingsKit
import XCTest

/// P7.6 destination rows: provisional leads vs checked fares (synthetic prices).
final class DiscoverRowsTests: XCTestCase {
    func lead(_ dest: String, _ date: String, _ amount: String) -> SelectedLead {
        SelectedLead(origin: "CGK", destination: dest, date: date, observationIndex: 0, comparableAmount: amount)
    }

    func checked(_ dest: String, _ date: String, _ amount: String) -> FoundOffer {
        let route = RouteDate(origin: "CGK", destination: dest, date: date)
        return FoundOffer(routeDate: route, index: Int(amount)!, offer: sourceOffer("fli", date, price: amount),
                          searchURL: URL(string: "https://example.invalid")!)
    }

    func summary(_ leads: [SelectedLead]) -> DiscoverySummary {
        var s = DiscoverySummary()
        s.selected = leads
        s.committed = true
        return s
    }

    func testLeadWithoutFareStaysProvisional() {
        let rows = discoverRows(summary: summary([lead("DPS", "2027-03-01", "640000")]), offers: [], currency: "IDR", finished: false)
        XCTAssertEqual(rows.map(\.destination), ["DPS"])
        XCTAssertEqual(rows[0].leadAmount, "640000")
        XCTAssertNil(rows[0].checkedOffer)
        XCTAssertEqual(rows[0].state, .checking)
        XCTAssertEqual(discoverRows(summary: summary([lead("DPS", "2027-03-01", "640000")]), offers: [], currency: "IDR",
                                    finished: true)[0].state, .noFare)
    }

    func testCheckedFirstByCheckedPriceAndOnlyTheLeadsDate() {
        let leads = [lead("DPS", "2027-03-01", "640000"), lead("SIN", "2027-03-01", "800000"), lead("BKK", "2027-03-02", "900000")]
        let offers = [checked("SIN", "2027-03-01", "750000"), checked("SIN", "2027-03-01", "990000"), checked("DPS", "2027-03-02", "100")]
        let rows = discoverRows(summary: summary(leads), offers: offers, currency: "IDR", finished: true)
        XCTAssertEqual(rows.map(\.destination), ["SIN", "DPS", "BKK"])
        XCTAssertEqual(rows[0].checkedOffer?.offer.priceComparable, "750000")
        XCTAssertEqual(rows.map(\.state), [.checked, .noFare, .noFare])
    }

    func testEmptyShortlistHasNoRows() {
        XCTAssertTrue(discoverRows(summary: summary([]), offers: [checked("SIN", "2027-03-01", "1")], currency: "IDR", finished: true).isEmpty)
    }
}
