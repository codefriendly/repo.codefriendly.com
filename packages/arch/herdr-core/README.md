# herdr-core Arch package

This package builds herdr-core from its release source and pinned Ghostty VT
source. It installs `/usr/bin/herdr-core` and the `hc` symlink. It does not install
the original Herdr terminal UI or the Herdr desktop application.

Build and test with:

```sh
scripts/build arch herdr-core
```

The recipe uses the Arch Rust toolchain and the checksummed Zig 0.16.0 toolchain.
Ghostty does not support Arch's current Zig release. Dependencies use Cargo.lock
and Ghostty's content-hashed Zig dependency declarations. Build and test commands
use Cargo's frozen mode after fetching sources. Only native x86_64 is supported
by this recipe. No AUR dependency or prebuilt application binary is used.

## Tests and operation

The recipe runs the upstream test suite, including real PTYs and isolated core
sessions. It uses upstream CI's watchdog and slow-runner timing settings.
It also checks the release version and embedded license notices.

The package has no installation hook and starts no service during installation.
Core starts on demand. Update the system package with `sudo pacman -Syu`.
Upstream detects an unwritable installation directory as package-manager-owned.
Do not run `hc update` through sudo to replace package files. Remote-machine
installation and updates remain upstream features and can download releases.

## Licenses

The application is Apache-2.0. Bundled components retain their original terms.
The recipe regenerates upstream's dependency notices, adds the BSD notice from
simdutf's TH-derived CPU detection code, and adds notices for the build's Rust
standard library and compiler runtime. These additions are embedded in
`hc --licenses` and installed with the application license.

The upstream aggregate also retains notices describing its Rust 1.95.0 and musl
release builds. Those entries do not identify this package's compiler or libc.
The appended Arch build section identifies the actual Rust compiler. This package
uses system glibc. The package also retains Zig and bundled runtime notices and
the complete simdutf header, including its in-header third-party terms.

Dependency and native-component changes need license review. A notice generator
or a passing test does not establish that every newly added component is covered.
For the Herdr package family, bundled media, font and icon licensing follows
upstream's declarations and attribution. This core release has no GUI media.

This is a repository-only package. It does not claim AUR maintainership.
Building it does not authorize signing, publication, or a website update.
