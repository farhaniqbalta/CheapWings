#!/bin/sh
# Builds the cheapwings-ffi Rust library for iPad/iPhone, iOS simulator and macOS, generates
# the UniFFI Swift bindings and packages both into apps/ios/CheapWingsCore (gitignored output).
set -eu
cd "$(dirname "$0")"
export PATH="$HOME/.cargo/bin:$PATH"
export DEVELOPER_DIR="${DEVELOPER_DIR:-/Applications/Xcode.app/Contents/Developer}"
# Match the Swift package minimums so C dependencies are not built for the newest OS only.
export IPHONEOS_DEPLOYMENT_TARGET=17.0 MACOSX_DEPLOYMENT_TARGET=13.0

for target in aarch64-apple-ios aarch64-apple-ios-sim aarch64-apple-darwin; do
    cargo build --release -p cheapwings-ffi --lib --target "$target"
done

pkg=../apps/ios/CheapWingsCore
module=cheapwings_ffiFFI
rm -rf build/bindings build/headers "$pkg/$module.xcframework"
cargo run -q --release -p cheapwings-ffi --bin uniffi-bindgen -- generate \
    --library target/aarch64-apple-darwin/release/libcheapwings_ffi.a --language swift --out-dir build/bindings
# Headers in a per-module folder so other XCFrameworks can coexist in one app.
mkdir -p "build/headers/$module" "$pkg/Sources/CheapWingsCore"
cp "build/bindings/$module.h" "build/headers/$module/"
cp "build/bindings/$module.modulemap" "build/headers/$module/module.modulemap"
cp build/bindings/cheapwings_ffi.swift "$pkg/Sources/CheapWingsCore/Generated.swift"

xcodebuild -create-xcframework \
    -library target/aarch64-apple-ios/release/libcheapwings_ffi.a -headers build/headers \
    -library target/aarch64-apple-ios-sim/release/libcheapwings_ffi.a -headers build/headers \
    -library target/aarch64-apple-darwin/release/libcheapwings_ffi.a -headers build/headers \
    -output "$pkg/$module.xcframework"
echo "built $pkg/$module.xcframework"
