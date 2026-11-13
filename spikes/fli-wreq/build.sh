#!/bin/sh
# Builds the S2 Rust library for iPhone, iOS simulator and macOS, generates the UniFFI Swift
# bindings and packages everything for the FliWreq Swift package in ./swift.
set -eu
cd "$(dirname "$0")"
export PATH="$HOME/.cargo/bin:$PATH"
export DEVELOPER_DIR="${DEVELOPER_DIR:-/Applications/Xcode.app/Contents/Developer}"
# Match the Swift packages' minimums so BoringSSL's C objects are not built for the newest OS only.
export IPHONEOS_DEPLOYMENT_TARGET=17.0 MACOSX_DEPLOYMENT_TARGET=13.0

for target in aarch64-apple-ios aarch64-apple-ios-sim aarch64-apple-darwin; do
    cargo build --release --lib --target "$target"
done

rm -rf build/bindings build/headers swift/fli_wreqFFI.xcframework
cargo run -q --release --bin uniffi-bindgen -- generate \
    --library target/aarch64-apple-darwin/release/libfli_wreq.a --language swift --out-dir build/bindings
mkdir -p build/headers swift/Sources/FliWreq
cp build/bindings/fli_wreqFFI.h build/headers/
cp build/bindings/fli_wreqFFI.modulemap build/headers/module.modulemap
cp build/bindings/fli_wreq.swift swift/Sources/FliWreq/Generated.swift

xcodebuild -create-xcframework \
    -library target/aarch64-apple-ios/release/libfli_wreq.a -headers build/headers \
    -library target/aarch64-apple-ios-sim/release/libfli_wreq.a -headers build/headers \
    -library target/aarch64-apple-darwin/release/libfli_wreq.a -headers build/headers \
    -output swift/fli_wreqFFI.xcframework
echo "built swift/fli_wreqFFI.xcframework"
