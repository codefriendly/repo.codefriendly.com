# Strata source package

The package name is `strata-fm`. The command and desktop application remain
`strata` and Strata. The recipe uses a checksummed stable release archive and
retains attribution to the AUR `strata-fm-git` recipe.

From the repository root, run:

```bash
scripts/build arch strata-fm --output /tmp/strata-build
```

This command needs Docker, not host build dependencies or sudo prompts.
It is also the entry point for a future CI build job. No CI workflow, signing,
upload, or automatic publication is configured by this recipe.

## Features and licensing

This package disables upstream's default `rar` feature. RAR extraction and CBR
cover previews are unavailable. PDF previews and the other archive formats remain
available. The build, tests, and Rust license report all use
`--no-default-features`.

Strata's source remains MIT-licensed. The executable links GPL-covered Poppler,
so this combined build is distributed under GPL-3.0-or-later. Original component
notices remain installed. Do not enable UnRAR in a published build: its use
restrictions are GPL-incompatible. The upstream source and third-party summary
still describe that optional component; this does not mean it is linked here.

Each build exports a matching `.src.tar.zst` archive beside the binary package.
It contains the application source, locked vendored Cargo dependencies, notices,
and package build files. The source archive retains optional dependencies for
the complete lockfile, including UnRAR, but the build does not compile them.
Publish that archive and the matching Poppler source/build files with the binary.
Do not treat the generated Rust report alone as complete source delivery.

Published source for this release is available at
<https://repo.codefriendly.com/arch/sources/strata-fm-1.1.1-2.src.tar.zst>.
The matching Poppler source and Arch build files are linked from
<https://repo.codefriendly.com/arch/sources/strata-fm-1.1.1-2-native-sources.txt>.

To rebuild from the source archive on Arch Linux, extract it into an empty
directory. Run these commands there. Dependency installation needs sudo.

```bash
mkdir src
cp -a strata-1.1.1 src/
cp README.md GPL-3.0.txt src/
makepkg --noextract --clean --syncdeps --noconfirm
```

`--noextract` retains the supplied vendored dependencies and generated notices.
The build and tests run with Cargo's frozen mode. The source archive is separate
from the installed package so users do not have to install development sources.

## Automated checks

- `prepare()` compares the application and bundled-asset notice files with
  `license-files.sha256`. A changed, missing, or added file stops the build.
- Cargo fetches the locked dependencies before compilation. The build and tests
  use `--frozen`, so they cannot change the lockfile or fetch missing dependencies.
- `cargo-about` generates `RUST-LICENSES.md` for the selected native dependency graph.
  `about.toml` defines the reviewed license choices. Unaccepted licenses stop
  the build. Checksum-verified clarifications retrieve missing notices from each
  crate's published Git commit. This step needs network access in `prepare()`.
  `rust-licenses.py` preserves the notices and rejects unreviewed generic fallbacks.
- `check()` validates the desktop entry, checks the release version, and runs
  the upstream Rust tests on a private Xvfb display and D-Bus session. A private
  test home shares the temporary filesystem so GIO can use Trash. The display
  uses upstream's 1280×1024 settings. GTK initialization must succeed.
  Device-dependent tests can still skip when their
  required devices or kernel features are absent. Tests for optional helpers can
  also skip when the helper is absent.
- `package()` installs the application notice, all bundled-asset license files,
  and the generated Rust notices. It also exports the source archive and its
  checksum. The shared builder exports metadata, a file inventory, a checksum,
  and an advisory Namcap report beside the package.

Rust notices are combined in `RUST-LICENSES.md`. Check the actual texts, not just
Namcap's notice-file count.
Its unused-dependency warnings for Bubblewrap, GVfs, and GStreamer plugins do
not detect their use as runtime helpers or dynamically loaded plugins.

## Updates

Update `pkgver` and the source archive checksum. Regenerate `.SRCINFO`, then run
the same build command. Do not refresh `license-files.sha256` just to pass a
failed build. Review changed notice text or a new bundled component first.
Changes outside the Rust license policy also require review. This gate does not
establish that upstream metadata is complete or replace a source-code audit.

Four crates need version-specific exceptions in `rust-licenses.py` because their
published archives omit notice files. Rquickjs has a checksummed upstream notice.
Siphasher has a checksummed copyright notice and references the standard MIT grant.
Poppler's two Rust crates declare MIT but supply no separate license or copyright
file at the published commit. Their original Cargo metadata and the standard MIT
grant are included without inventing a copyright statement. A new version of any
of these four crates requires review before the exception can change.

The upstream UnRAR notice remains installed because the upstream third-party
summary links to it. No UnRAR code is compiled into this build. GTK, GStreamer,
and Poppler are supplied by Arch packages. The experimental upstream
media-runtime patch kit is not built or installed by this recipe.

File-manager and portal integration remain per-user opt-ins. The install-source
marker identifies `strata-fm` as pacman-managed, so in-app updates do not replace
the package-owned executable. The source archive is shared by x86_64 and aarch64;
each architecture still needs its own native build test.
