# Herdr CLI Arch package

This package builds CodeFriendly's Herdr fork, release `codefriendly-v0.9.5-r1`,
from integration commit `78b1b52b6f57ba63a818519e06e6a878d06bb430`.
Its tree is `80e190bbb431131b8249af2e71fcead9002a8106`. It contains upstream
0.9.5 plus the pane-hover-focus patch set. The Arch package version is
`0.9.5+codefriendly1`; the executable reports `herdr 0.9.5`.
It installs `/usr/bin/herdr` and Bash, Fish and Zsh completions.
Only native x86_64 is supported.

The source is not fork master: that branch holds maintenance files and exported
patches without the enabled feature. This recipe pins the integration commit,
which matches the fork's release tag and recorded profile. It does not build
from a moving local checkout. Cargo dependencies and licenses match upstream
0.9.5 at `2ecf19a92fc3a7fff75b6ce3655ef04f4625ec01`.

Build and test with `scripts/build arch herdr`. The recipe uses the Arch Rust
toolchain and checksummed Zig 0.16.0. Cargo.lock and Zig content hashes verify
dependency downloads. Cargo builds and tests use frozen mode after fetching.
The check function runs all workspace Rust tests with upstream's nextest runner,
including hover tests. It also runs the Python vendor, UI architecture,
configuration and agent-manifest contract tests, then checks the version and
hover setting. This is not the full upstream maintenance suite: Windows SDK
checks and Bun-based documentation/integration tests are not run by the recipe.

## Runtime and updates

Herdr 0.9.5 contains its own server and terminal runtime. It does not invoke
`hc` or `herdr-core`. Installing herdr-core is not required and does not replace
the CLI's statically linked Ghostty library. This package can coexist with
herdr-core. It does not run the upstream installer or install a private core.

No installation hook starts a service or changes user configuration. Herdr starts
its server on demand. Use `sudo pacman -Syu` to update this package.
CodeFriendly modified `src/main.rs` on 2026-10-30 with `pacman-update.patch`.
The local `herdr update` command now prints package-manager guidance and exits
successfully without checking for updates, downloading files or replacing the
executable. The `--handoff` option also uses this guidance. Argument validation
and help remain unchanged.

This patch changes only the local update command. Channel commands, background
update checks and remote installation remain unchanged. Remote installers
select upstream binaries, not this fork's package. Install this package on
remote Arch machines if they must use the same patched build.
Background update checks and remote installation can use curl and download files.
Remote connections need OpenSSH. Sound and clipboard tools are optional.

## Licenses and security review

The first-party code is Apache-2.0, including bundled integration scripts and
sound assets under the repository license. Upstream supplies no separate sound
attribution. This relies on upstream's license declaration; it is not an
independent audit of asset authorship. No GUI font or icon assets are installed.
The obsolete AGPL metadata from AUR does not describe this upstream revision.

`licenses.py` collects notices from the locked Linux Cargo dependency graph,
including vendored portable-pty. It rejects unreviewed license expressions and
missing license files. It also retains Ghostty, downloaded Zig dependency,
Unicode data, simdutf, and Rust and Zig runtime notices. The complete simdutf
amalgamations preserve in-source attribution and the BSD CPU detection grant.
The recipe adds simdutf 9.0.0's MIT license from its official tag. It also adds
the missing Ratatui 0.30.0 family licenses from the crates' recorded source commit,
`0a2a7c0363a4806b0cf05c1915bf7cdd438f756c`.
It supplements vtparse and wezterm-input-types with the MIT notices from each
crate's recorded WezTerm source commit. The generator checks those commit IDs.
The notice inventory includes optional crates in Cargo's resolved graph;
not every listed crate is linked into the Linux executable.
Review dependency and native license changes before updating this recipe.

The source recipe was imported without history from AUR herdr commit
`1461f14c3827d2b2f3460dcb1142fda4c169706e`. Its original placeholder maintainer
line remains in PKGBUILD. AUR herdr-bin was also inspected but not imported.
The recipe uses HTTPS, pinned application source, SHA-256 checksums and locked
dependency graphs. It runs build scripts as an unprivileged container user.
It has no installation hook or privileged launcher. This packaging review does
not establish that all upstream code or dependencies are safe.

This source recipe does not claim AUR maintainership or authorize publication.
