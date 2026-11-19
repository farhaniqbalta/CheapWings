#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
revision=$(sh core/source-revision.sh)
printf 'EXPECTED_REVISION = "%s"\n' "$revision" > backend/src/cheapwings/_core_revision.py
printf 'let expectedCoreRevision = "%s"\n' "$revision" > apps/ios/CheapWingsCore/Sources/CheapWingsCore/ExpectedCoreRevision.swift
