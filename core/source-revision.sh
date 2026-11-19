#!/bin/sh
set -eu
cd "$(dirname "$0")"
{
    printf '%s\n' Cargo.toml Cargo.lock source-revision.sh
    find cheapwings-core cheapwings-py cheapwings-ffi cheapwings-store -type f \( -name '*.rs' -o -name Cargo.toml \) ! -path '*/tests/*'
} | LC_ALL=C sort | while IFS= read -r file; do
    shasum -a 256 "$file"
done | shasum -a 256 | cut -d ' ' -f 1
