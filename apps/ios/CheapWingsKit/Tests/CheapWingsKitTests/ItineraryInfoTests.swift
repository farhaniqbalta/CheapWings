import CheapWingsCore
@testable import CheapWingsKit
import XCTest

final class ItineraryInfoTests: XCTestCase {
    func leg(_ o: String, _ d: String, _ depart: String, _ arrive: String) -> FliLeg {
        FliLeg(origin: o, destination: d, airline: "NH", flightNumber: "856", departLocal: depart, arriveLocal: arrive)
    }

    func testItineraryDurationsAcrossTimeZones() {
        // CGK (UTC+7) 21:45 → HND (UTC+9) 07:00 next day = 7 h 15 m.
        let offer = FliOffer(price: "11292200", currency: "IDR", legs: [leg("CGK", "HND", "2026-12-15T21:45", "2026-12-16T07:00")])
        let info = ItineraryInfo.make(offer: offer, catalog: testCatalog)
        XCTAssertEqual(info.stops, 0)
        XCTAssertEqual(info.totalMinutes, 435)
        XCTAssertEqual(info.legMinutes, [435])
        XCTAssertTrue(info.layovers.isEmpty)
        XCTAssertTrue(info.airportChanges.isEmpty)
    }

    func testLayoverAcrossTimeZones() {
        // CGK 09:30 → SIN 12:10 (UTC+8), layover, SIN 14:05 → HND 22:00 (UTC+9).
        let offer = FliOffer(price: "1", currency: "IDR", legs: [
            leg("CGK", "SIN", "2026-12-15T09:30", "2026-12-15T12:10"),
            leg("SIN", "HND", "2026-12-15T14:05", "2026-12-15T22:00"),
        ])
        let info = ItineraryInfo.make(offer: offer, catalog: testCatalog)
        XCTAssertEqual(info.stops, 1)
        XCTAssertEqual(info.legMinutes, [100, 415])
        XCTAssertEqual(info.layovers, [Layover(airport: "SIN", toAirport: nil, minutes: 115)])
        XCTAssertEqual(info.totalMinutes, 630)
    }

    func testLayoverAndAirportChange() {
        let offer = FliOffer(price: "1", currency: "IDR", legs: [
            leg("CGK", "NRT", "2026-12-15T06:00", "2026-12-15T15:00"),
            leg("HND", "ITM", "2026-12-15T18:00", "2026-12-15T19:10"),
        ])
        let info = ItineraryInfo.make(offer: offer, catalog: testCatalog)
        XCTAssertEqual(info.airportChanges, [AirportChange(from: "NRT", to: "HND")])
        XCTAssertEqual(info.layovers, [Layover(airport: "NRT", toAirport: "HND", minutes: 180)])
    }

    func testMissingTimezoneOmitsDuration() {
        let offer = FliOffer(price: "1", currency: "IDR", legs: [leg("CGK", "QQQ", "2026-12-15T06:00", "2026-12-15T08:00")])
        let info = ItineraryInfo.make(offer: offer, catalog: testCatalog)
        XCTAssertNil(info.totalMinutes)
        XCTAssertEqual(info.legMinutes, [nil])
    }

    func testInconsistentTimesGiveNoDuration() {
        // Arrival before departure (bad data) must read "unknown", never "-1h".
        let offer = FliOffer(price: "1", currency: "IDR", legs: [leg("CGK", "DPS", "2026-12-15T10:00", "2026-12-15T08:00")])
        let info = ItineraryInfo.make(offer: offer, catalog: testCatalog)
        XCTAssertEqual(info.legMinutes, [nil])
        XCTAssertNil(info.totalMinutes)
    }

    func testSpokenDuration() {
        XCTAssertEqual(ItineraryInfo.spokenDuration(435), "7 hours 15 minutes")
        XCTAssertEqual(ItineraryInfo.spokenDuration(60), "1 hour")
        XCTAssertEqual(ItineraryInfo.spokenDuration(1), "1 minute")
    }

    func testDurationText() {
        XCTAssertEqual(ItineraryInfo.durationText(435), "7h 15m")
        XCTAssertEqual(ItineraryInfo.durationText(60), "1h")
        XCTAssertEqual(ItineraryInfo.durationText(45), "45m")
    }
}
