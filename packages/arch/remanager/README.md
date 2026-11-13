# reManager source package

This package builds reManager 2.0.0 from its checksummed upstream release
source. The package name is `remanager`. The executable remains
`/usr/bin/reManager`. It conflicts with `remanager-bin`. No AUR publication is
configured.

## Build and test

From the repository root, run:

```bash
scripts/build arch remanager --output /tmp/remanager-build
```

The container installs Go, Node.js, npm, GTK 4, and WebKitGTK 6.0. Wails v3
builds with plain `go build`; the recipe drives the steps that upstream's
`wails3 task linux:build` performs rather than installing the Task runner. npm
uses the upstream lockfile with lifecycle scripts disabled. Application compilation
uses vendored Go modules. The Wails CLI uses a local module mirror containing its
separate dependency graph. Neither compilation step resolves dependencies over
the network.
Upstream Go tests and desktop entry validation must pass before the package is
created.

reManager 2.0.0 pins Wails v3 through a `replace` directive to
`third_party/wails-v3`, which the release archive does not contain. The recipe
runs upstream's `scripts/prepare-wails-fork.sh`, which copies the pinned module
from the Go module cache and applies `build/wails-patches/*.patch`. The patches
touch only the iOS and Android backends. The recipe then builds the `wails3`
CLI from that fork and regenerates `frontend/bindings` before the frontend is
built, so the TypeScript bindings always match the compiled Go services.

Only native x86_64 is advertised and tested. GUI startup does not prove tablet
connections, firmware changes, package installation, or password storage work.
Those actions need a reMarkable tablet and explicit user approval.

The application still reports upstream releases. Install package updates with
pacman. GNOME Keyring is optional for saved passwords. Do not run reManager as
root.

## Licenses and source delivery

Upstream licenses reManager under GPLv3. The package preserves its license,
the Go runtime license, and original Go and frontend dependency notices.
The statically linked `remarkable-go` library uses LGPLv3. The source archive
includes its source and the application source so recipients can rebuild with
a modified library. It also contains the patched Wails v3 tree. Publish this
source archive with every binary release. The pinned Go license checker and the
npm license checker stop on licenses outside the reviewed allowlists. This is
not a full upstream security audit or a legal opinion.

Some npm tarballs omit their MIT notice. The recipe supplies the original
Radix UI notice from commit `fcef0668a5c827e5a4baac405474d75680f9a4eb`, the
`react-remove-scroll-bar` notice added upstream in commit
`7301c160fda44cb8cf2b9fdfde61efad35736196`, and the Wails notice at tag
`v3.0.0-beta.26`. All three sources have fixed checksums.

Each build exports `remanager-2.0.0-1.src.tar.zst` and its SHA-256 checksum
beside the binary. Publish this archive with the binary. It contains the
release source archive, prepared source, vendored Go modules, a Go module
download mirror, locked npm dependencies, generated bindings and notices,
and the package recipe. The application binary and compiler caches are not
included. Build tools in npm dependencies retain their original terms.

To rebuild the prepared source on x86_64 Arch Linux, extract the source archive
into an empty directory, then run:

```bash
mkdir src
cp -a reManager-2.0.0 src/
makepkg --noextract --clean --syncdeps --noconfirm
```

`--noextract` skips the network-dependent `prepare()` step and preserves the
delivered frontend dependencies, patched Wails tree, and generated notices.
`build()` restores the included module mirror into its private GOPATH cache;
no existing Go module cache or separate cache-seeding command is needed.
With the Arch build and check dependencies already installed, compilation and
tests can run without network access. `--syncdeps` needs network access if pacman
must install missing dependencies.

The Arch build dependencies must be available through pacman. Signing and
publication are separate local release steps. Do not put signing keys in
the build container. Do not mark a version as published until the signed
binary, signed database, and source archive are available on the server.
