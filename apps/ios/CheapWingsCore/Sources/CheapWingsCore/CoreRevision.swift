import cheapwings_ffiFFI

func coreRevisionError(_ actual: String) -> String? {
    actual == expectedCoreRevision ? nil : "CheapWings core revision mismatch. Run core/build-ios.sh."
}

func verifyCoreRevision() {
    if let error = coreRevisionError(String(cString: cheapwings_core_build_revision())) {
        fatalError(error)
    }
}
