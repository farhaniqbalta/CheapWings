#!/bin/sh
# Builds the S5 Rust core for iPhone/iPad, iOS simulator and macOS and packages it as the
# RustCore Swift package in ../rust-swift (XCFramework + UniFFI bindings).
set -eu
cd "$(dirname "$0")"
export PATH="$HOME/.cargo/bin:$PATH"
export DEVELOPER_DIR="${DEVELOPER_DIR:-/Applications/Xcode.app/Contents/Developer}"
export IPHONEOS_DEPLOYMENT_TARGET=17.0 MACOSX_DEPLOYMENT_TARGET=13.0

for target in aarch64-apple-ios aarch64-apple-ios-sim aarch64-apple-darwin; do
    cargo build --release --lib --target "$target"
done

out=../rust-swift
rm -rf build "$out/core_s5FFI.xcframework"
cargo run -q --release --bin uniffi-bindgen -- generate \
    --library target/aarch64-apple-darwin/release/libcore_s5.a --language swift --out-dir build/bindings
# Headers in a per-module subfolder so several XCFrameworks can coexist in one app.
mkdir -p build/headers/core_s5FFI "$out/Sources/RustCore"
cp build/bindings/core_s5FFI.h build/headers/core_s5FFI/
cp build/bindings/core_s5FFI.modulemap build/headers/core_s5FFI/module.modulemap
cp build/bindings/core_s5.swift "$out/Sources/RustCore/Generated.swift"

xcodebuild -create-xcframework \
    -library target/aarch64-apple-ios/release/libcore_s5.a -headers build/headers \
    -library target/aarch64-apple-ios-sim/release/libcore_s5.a -headers build/headers \
    -library target/aarch64-apple-darwin/release/libcore_s5.a -headers build/headers \
    -output "$out/core_s5FFI.xcframework"
echo "built $out/core_s5FFI.xcframework"
