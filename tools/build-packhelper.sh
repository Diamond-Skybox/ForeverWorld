#!/bin/sh
# Compiles tools/PackHelper.java into PackHelper.jar at the pack root (Java 17 bytecode, runs on any Java 17+ runtime), then refreshes the index.
set -e
cd "$(dirname "$0")/.."
out=$(mktemp -d)
javac --release 17 -d "$out" tools/PackHelper.java
jar --create --file PackHelper.jar --main-class PackHelper -C "$out" .
rm -rf "$out"
packwiz refresh
