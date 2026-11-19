@testable import CheapWingsCore
import XCTest

final class CoreRevisionTests: XCTestCase {
    func testRevisionMismatchNamesRebuildCommand() {
        XCTAssertNil(coreRevisionError(expectedCoreRevision))
        XCTAssertEqual(coreRevisionError("stale"),
                       "CheapWings core revision mismatch. Run core/build-ios.sh.")
    }
}
