#!/bin/sh
# Build the official RTR-Netztest client (Open-RMBT, clientC) as a static binary.
# Runs inside alpine:3.24 (musl); the result runs on any Linux of the same CPU architecture.
# Usage: build-rmbt-client.sh <rtr-commit> <output-file>
set -eu

COMMIT="$1"
OUT="$2"

apk add --no-cache gcc make musl-dev git binutils pkgconf \
    openssl-dev openssl-libs-static curl-dev curl-static nghttp2-dev nghttp2-static \
    zlib-static brotli-static zstd-static c-ares-dev libidn2-static libpsl-static libunistring-static >/dev/null

git clone --quiet https://github.com/rtr-nettest/open-rmbt-client-cli.git /src
cd /src
git checkout --quiet "$COMMIT"
cd clientC
make -s LDFLAGS="$(pkg-config --static --libs libcurl openssl) -lpthread -static"
strip build/rmbt-client

# Must be fully static and start.
if ldd build/rmbt-client 2>&1 | grep -q "=>"; then
    echo "binary is not static" >&2
    exit 1
fi
build/rmbt-client --help >/dev/null

cp build/rmbt-client "$OUT"
echo "built $(basename "$OUT") from rtr-nettest/open-rmbt-client-cli@$COMMIT"
