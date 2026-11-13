import FliWreq
import Foundation

if let error = WreqProbe.clientBuildError() {
    print("wreq client build FAILED: \(error)")
    exit(1)
}
print("wreq client build OK")
