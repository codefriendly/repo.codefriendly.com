#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 CodeFriendly
# SPDX-License-Identifier: MIT
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
for tool in git makepkg python3 uv; do
  command -v "$tool" >/dev/null || { echo "Missing test prerequisite: $tool" >&2; exit 1; }
done
[[ $EUID -ne 0 ]] || { echo 'Run these tests as an unprivileged user.' >&2; exit 1; }

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

# Isolate Git identity/config and rewrite both AUR transports to a local fixture.
# Disallow all other protocols so a broken rewrite cannot reach a real remote.
export GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1 GIT_ALLOW_PROTOCOL=file
export GIT_CONFIG_COUNT=5
export GIT_CONFIG_KEY_0=user.name GIT_CONFIG_VALUE_0='Packaging tests'
export GIT_CONFIG_KEY_1=user.email GIT_CONFIG_VALUE_1=tests@localhost
export GIT_CONFIG_KEY_2=commit.gpgsign GIT_CONFIG_VALUE_2=false
export GIT_CONFIG_KEY_3="url.file://$tmp/aur/.insteadOf"
export GIT_CONFIG_VALUE_3=https://aur.archlinux.org/
export GIT_CONFIG_KEY_4="url.$tmp/aur/.insteadOf"
export GIT_CONFIG_VALUE_4=ssh://aur@aur.archlinux.org/

expect_failure() {
  if "$@" > "$tmp/failure.log" 2>&1; then
    echo "Expected failure: $*" >&2
    exit 1
  fi
}

mkdir -p "$tmp/aur" "$tmp/monorepo/scripts"
git init --quiet --initial-branch=master "$tmp/package"
cat > "$tmp/package/PKGBUILD" <<'PKGBUILD'
pkgname=layout-fixture
pkgver=1.0
pkgrel=1
pkgdesc='Local fixture for packaging path tests'
arch=(any)
url=https://example.invalid
license=(MIT)
package() { :; }
PKGBUILD
(cd "$tmp/package" && makepkg --printsrcinfo > .SRCINFO)
git -C "$tmp/package" add PKGBUILD .SRCINFO
git -C "$tmp/package" commit --quiet -m 'Initial fixture'
aur_tip=$(git -C "$tmp/package" rev-parse HEAD)
git clone --quiet --bare "$tmp/package" "$tmp/aur/layout-fixture.git"

cp "$repo_root/scripts/adopt" "$repo_root/scripts/publish" "$repo_root/scripts/catalog.py" "$tmp/monorepo/scripts/"
git init --quiet --initial-branch=main "$tmp/monorepo"
cd "$tmp/monorepo"
git add scripts
git commit --quiet -m 'Initial test monorepo'
initial=$(git rev-parse HEAD)

# Non-maintainers copy the recipe without adding upstream commits or Git metadata.
git clone --quiet "$tmp/monorepo" "$tmp/snapshot"
(
  cd "$tmp/snapshot"
  expect_failure bash scripts/adopt layout-fixture </dev/null
  grep -q 'Specify --aur-maintainer or --no-aur-maintainer' "$tmp/failure.log"
  expect_failure bash scripts/adopt --aur-maintainer --no-aur-maintainer layout-fixture
  bash scripts/adopt --no-aur-maintainer --dry-run layout-fixture > "$tmp/snapshot-dry-run.log" 2>&1
  [[ $(git rev-parse HEAD) == "$initial" && ! -e packages/arch/layout-fixture ]]
  printf 'n\n' | bash scripts/adopt layout-fixture > "$tmp/snapshot.log" 2>&1
  cmp "$tmp/package/PKGBUILD" packages/arch/layout-fixture/PKGBUILD
  cmp "$tmp/package/.SRCINFO" packages/arch/layout-fixture/.SRCINFO
  [[ ! -e packages/arch/layout-fixture/.git && $(git rev-parse HEAD) == "$initial" ]]
  git diff --cached --exit-code
  git add packages/arch/layout-fixture
  git commit --quiet -m 'Import recipe snapshot'
  [[ $(git rev-list --count HEAD) == 2 ]]
  [[ $(git rev-parse HEAD^) == "$initial" ]]
  expect_failure git merge-base --is-ancestor "$aur_tip" HEAD
)
printf 'PASS: non-maintainer import copies files without upstream history or an automatic commit\n'

bash scripts/adopt --aur-maintainer --dry-run layout-fixture > "$tmp/adopt-dry-run.log" 2>&1
[[ $(git rev-parse HEAD) == "$initial" && ! -e packages/arch/layout-fixture ]]
printf 'y\n' | bash scripts/adopt layout-fixture > "$tmp/adopt.log" 2>&1
[[ -f packages/arch/layout-fixture/PKGBUILD && ! -e layout-fixture ]]
split=$(git subtree split --prefix=packages/arch/layout-fixture 2> "$tmp/split.log")
[[ $split == "$aur_tip" ]]
expect_failure bash scripts/adopt layout-fixture
grep -q 'already exists' "$tmp/failure.log"
printf 'PASS: adoption uses nested paths and preserves imported history\n'

touch packages/arch/layout-fixture/local-change
cat > packages/arch/manifest.toml <<'MANIFEST'
[layout-fixture]
binary_repo = false
aur_maintainer = true
MANIFEST
git add packages/arch/layout-fixture/local-change packages/arch/manifest.toml
git commit --quiet -m 'Local fixture change'
bash scripts/publish --dry-run layout-fixture > "$tmp/publish.log" 2>&1
[[ $(git --git-dir="$tmp/aur/layout-fixture.git" rev-parse master) == "$aur_tip" ]]
split=$(git subtree split --prefix=packages/arch/layout-fixture 2> "$tmp/updated-split.log")
git merge-base --is-ancestor "$aur_tip" "$split"
printf 'PASS: publication validates metadata and previews a fast-forward without changing the remote\n'
python3 scripts/catalog.py --allow-aur layout-fixture
expect_failure python3 scripts/catalog.py --allow-binary layout-fixture
expect_failure python3 scripts/catalog.py --allow-aur unreviewed
expect_failure python3 scripts/catalog.py --allow-binary unreviewed
printf 'PASS: publication targets are opt-in; AUR-only and unreviewed binaries rejected\n'

expect_failure bash scripts/adopt ../escape
expect_failure bash scripts/publish ../escape
expect_failure bash scripts/publish missing-package
touch untracked-file
expect_failure bash scripts/adopt another-fixture
grep -q 'dirty worktree' "$tmp/failure.log"
expect_failure bash scripts/publish layout-fixture
grep -q 'dirty worktree' "$tmp/failure.log"
rm untracked-file
printf 'PASS: invalid paths, absent packages, and dirty worktrees rejected\n'

printf '\n# Deliberately stale test metadata\n' >> packages/arch/layout-fixture/.SRCINFO
git add packages/arch/layout-fixture/.SRCINFO
git commit --quiet -m 'Deliberately stale fixture metadata'
expect_failure bash scripts/publish --dry-run layout-fixture
grep -q 'is stale' "$tmp/failure.log"
printf 'PASS: stale SRCINFO rejected\n'

# Source links follow the published version, not the local recipe version.
mkdir site
cp -r "$repo_root/site/templates" site/
cp "$repo_root/scripts/catalog.py.lock" scripts/
printf '<!-- package-catalog:start --><!-- package-catalog:end -->\n' > README.md
cp -r packages/arch/layout-fixture packages/arch/aur-fixture
cat > packages/arch/manifest.toml <<'MANIFEST'
[layout-fixture]
binary_repo = true
aur_maintainer = false
published_version = "2.4.0-3"
architecture = "aarch64"
source_archive = true
description = 'A <tool> & helper'

[aur-fixture]
binary_repo = false
aur_maintainer = true
description = 'AUR-only fixture'
MANIFEST
expect_failure uv run --locked scripts/catalog.py --check
[[ ! -e site/dist ]]
uv run --locked scripts/catalog.py
uv run --locked scripts/catalog.py --check
grep -Fq 'A &lt;tool&gt; &amp; helper' site/dist/packages.html
grep -Fq 'href="https://aur.archlinux.org/packages/aur-fixture"' site/dist/packages.html
! sed -n '/<section id="binary-repository"/,/<section id="aur"/p' site/dist/packages.html | grep -Fq 'aur-fixture'
grep -Fq 'href="https://repo.codefriendly.com/arch/sources/layout-fixture-2.4.0-3.src.tar.zst">Source archive</a>' site/dist/packages.html
printf '\nStale output\n' >> site/dist/index.html
cp site/dist/index.html "$tmp/stale-index.html"
expect_failure uv run --locked scripts/catalog.py --check
cmp site/dist/index.html "$tmp/stale-index.html"
sed -i 's/source_archive = true/source_archive = false/' packages/arch/manifest.toml
uv run --locked scripts/catalog.py
uv run --locked scripts/catalog.py --check
[[ $(grep -c 'Source archive' site/dist/packages.html) == 0 ]]
printf 'PASS: site generation escapes text, separates AUR packages, detects stale output without writes, and preserves source archive opt-in/version rules\n'

# Recording updates one package in place; retries preserve its timestamp.
! grep -q 'id="updates-title"' site/dist/index.html
python3 scripts/catalog.py --sync-package-review
[[ ! -e PACKAGE-REVIEW.local.md ]]
cat > PACKAGE-REVIEW.local.md <<'REVIEW'
Private review findings before.
<!-- package-publications:start -->
Stale publication state.
<!-- package-publications:end -->
Private review findings after.
REVIEW
python3 scripts/catalog.py --sync-package-review
grep -Fq '| layout-fixture | 2.4.0-3 | Not recorded | No |' PACKAGE-REVIEW.local.md
grep -Fq '| aur-fixture | Not published in this repository | Not recorded | Yes |' PACKAGE-REVIEW.local.md
grep -Fxq 'Private review findings before.' PACKAGE-REVIEW.local.md
grep -Fxq 'Private review findings after.' PACKAGE-REVIEW.local.md
! grep -q 'Stale publication state' PACKAGE-REVIEW.local.md
expect_failure python3 scripts/catalog.py --record-release aur-fixture 1.0-1
expect_failure python3 scripts/catalog.py --record-release layout-fixture ../invalid
expect_failure python3 scripts/catalog.py --record-release layout-fixture 2.4.0-3 --published-at 2999-01-01T00:00:00Z
expect_failure python3 scripts/catalog.py --record-release layout-fixture 2.4.0-3 --published-at 2026-01-01T00:00:00
python3 scripts/catalog.py --record-release layout-fixture 2.4.0-3 --published-at 2026-01-02T10:00:00Z
cp packages/arch/manifest.toml "$tmp/manifest.toml"
python3 scripts/catalog.py --record-release layout-fixture 2.4.0-3
cmp packages/arch/manifest.toml "$tmp/manifest.toml"
python3 scripts/catalog.py --record-release layout-fixture 2.4.1-1 --published-at 2026-01-02T11:00:00Z
grep -Fq '| layout-fixture | 2.4.1-1 | 2026-01-02 | No |' PACKAGE-REVIEW.local.md
! grep -q '2.4.0-3' PACKAGE-REVIEW.local.md
uv run --locked scripts/catalog.py
grep -q 'href="./packages.html#package-layout-fixture"' site/dist/index.html
grep -q 'id="package-layout-fixture"' site/dist/packages.html
grep -q 'layout-fixture-2.4.1-1-aarch64.pkg.tar.zst' site/dist/packages.html
[[ $(grep -c 'href="./packages.html#package-layout-fixture"' site/dist/index.html) == 1 ]]
! grep -q '2.4.0-3' site/dist/index.html

# Same-day timestamps, not package names or file order, determine the latest five.
for hour in 3 1 6 2 5 4; do
  cp -r packages/arch/layout-fixture "packages/arch/recent-$hour"
  cat >> packages/arch/manifest.toml <<MANIFEST

[recent-$hour]
binary_repo = true
aur_maintainer = false
published_version = "$hour-1"
published_at = 2026-01-03T0$hour:00:00Z
architecture = "x86_64"
MANIFEST
done
uv run --locked scripts/catalog.py
python3 - <<'PY'
from pathlib import Path
from html.parser import HTMLParser
class Updates(HTMLParser):
    active = False
    versions = []
    def handle_starttag(self, tag, attrs):
        if tag == 'ul' and ('class', 'updates') in attrs:
            self.active = True
    def handle_endtag(self, tag):
        if tag == 'ul':
            self.active = False
    def handle_data(self, data):
        if self.active and data.endswith('-1'):
            self.versions.append(data)
parser = Updates()
parser.feed(Path('site/dist/index.html').read_text())
assert parser.versions == ['6-1', '5-1', '4-1', '3-1', '2-1'], parser.versions
PY
printf 'PASS: latest package publications are validated, retry-safe, unique and sorted by timestamp\n'

# Approval permits staging, but only a verified publication adds catalog links.
cp -r packages/arch/layout-fixture packages/arch/pending-fixture
cat >> packages/arch/manifest.toml <<'MANIFEST'

[pending-fixture]
binary_repo = true
aur_maintainer = false
architecture = "x86_64"
MANIFEST
python3 scripts/catalog.py --allow-binary pending-fixture
uv run --locked scripts/catalog.py
! grep -q 'pending-fixture' site/dist/packages.html README.md
python3 scripts/catalog.py --sync-package-review
grep -Fq '| pending-fixture | Not published in this repository | Not recorded | No |' PACKAGE-REVIEW.local.md
python3 scripts/catalog.py --record-release pending-fixture 3.0-2 --published-at 2026-01-04T02:30:00Z
uv run --locked scripts/catalog.py
grep -Fq 'pending-fixture-3.0-2-x86_64.pkg.tar.zst' site/dist/packages.html
grep -Fq '| pending-fixture | 3.0-2 | 2026-01-04 | No |' PACKAGE-REVIEW.local.md
printf 'PASS: new approved packages stay unlisted until their first verified publication\n'
