#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 CodeFriendly
# SPDX-License-Identifier: MIT
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
mkdir -p "$tmp/repo/scripts" "$tmp/repo/packages/arch/build-fixture"
cp "$repo_root/scripts/build" "$repo_root/scripts/build-arch" "$tmp/repo/scripts/"
cp -r "$repo_root/docker" "$tmp/repo/"
build="$tmp/repo/scripts/build"
recipe="$tmp/repo/packages/arch/build-fixture"

expect_failure() {
  if "$@" > "$tmp/failure.log" 2>&1; then
    echo "Expected failure: $*" >&2
    exit 1
  fi
}
expect_failure "$build" deb build-fixture
expect_failure "$build" arch ../build-fixture
expect_failure "$build" arch missing-package

cat > "$recipe/PKGBUILD" <<'PKGBUILD'
pkgname=build-fixture
pkgver=1.0
pkgrel=1
pkgdesc='Container build test'
arch=(any)
license=(MIT)
makedepends=(jq python)
source=(payload .extra)
sha256sums=(SKIP SKIP)
build() {
  [[ $EUID -ne 0 ]]
  jq -n true
  # Tests can execute temporary helpers and create unnamed temporary files.
  helper=$(mktemp /tmp/build-helper.XXXXXX)
  printf '#!/bin/sh\nexit 0\n' > "$helper"
  chmod +x "$helper"
  "$helper"
  python -c 'import os; fd = os.open("/tmp", os.O_TMPFILE | os.O_RDWR, 0o600); os.write(fd, b"temporary"); os.lseek(fd, 0, 0); assert os.read(fd, 9) == b"temporary"; os.close(fd)'
  cat payload .extra > result
}
package() {
  install -Dm644 result "$pkgdir/usr/share/build-fixture/result"
}
PKGBUILD
printf 'source payload\n' > "$recipe/payload"
printf 'hidden helper\n' > "$recipe/.extra"
"$build" arch build-fixture --output "$tmp/success"
package=$(find "$tmp/success" -name '*.pkg.tar.zst' -print -quit)
[[ -n $package && -O $package && -s $tmp/success/.SRCINFO ]]
printf 'source payload\nhidden helper\n' > "$tmp/expected"
tar -xOf "$package" usr/share/build-fixture/result > "$tmp/result"
cmp "$tmp/expected" "$tmp/result"
grep -qx 'pkgname = build-fixture' "$package.PKGINFO"
grep -qx 'pkgver = 1.0-1' "$package.PKGINFO"
grep -qx 'usr/share/build-fixture/result' "$package.files"
[[ -s $package.namcap.log ]]
(cd "$tmp/success" && sha256sum --check "${package##*/}.sha256")
[[ ! -e $recipe/src && ! -e $recipe/pkg ]]
expect_failure "$build" arch build-fixture --output "$tmp/success"
# Checked-in metadata must match the recipe before a build can start.
cp "$tmp/success/.SRCINFO" "$recipe/.SRCINFO"
sed -i 's/pkgver = 1.0/pkgver = 0.9/' "$recipe/.SRCINFO"
expect_failure "$build" arch build-fixture --output "$tmp/stale"
grep -q 'Stale .SRCINFO' "$tmp/stale/build.log"
cp "$tmp/success/.SRCINFO" "$recipe/.SRCINFO"
# A failed build must return failure and retain its diagnostic output.
sed -i 's/  jq -n true/  echo deliberate-build-failure; return 1/' "$recipe/PKGBUILD"
expect_failure "$build" arch build-fixture --output "$tmp/failed"
grep -q deliberate-build-failure "$tmp/failed/build.log"
[[ -s $tmp/failed/.SRCINFO ]]
# Opt-in repository dependencies must install and run inside the container.
rm "$recipe/.SRCINFO"
sed -i 's/makedepends=(jq python)/makedepends=(jq python)\ndepends=(herdr-core)/; s/  echo deliberate-build-failure; return 1/  hc --version; jq -n true/' "$recipe/PKGBUILD"
"$build" arch build-fixture --codefriendly-repo --output "$tmp/repository"
grep -q '^hc ' "$tmp/repository/build.log"
package=$(find "$tmp/repository" -name '*.pkg.tar.zst' -print -quit)
grep -qx 'depend = herdr-core' "$package.PKGINFO"
echo 'Container build tests passed.'
