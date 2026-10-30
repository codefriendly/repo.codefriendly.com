# Pangolin source package

This package builds the official Fossorial Pangolin CLI from a checksummed
stable source archive. The package and command are both named `pangolin`.
It conflicts with `pangolin-bin`. No AUR publication is configured.

From the repository root, run:

```bash
scripts/build arch pangolin --output /tmp/pangolin-build
```

The Docker builder installs package-specific dependencies and runs the build,
upstream Go tests, version check, and updater check. No host Go installation
or interactive sudo is needed. Signing and publication are separate actions.

## Package-manager updates

The build sets upstream's `ManagedBy` variable to `pacman`. Update checks are
disabled by default. A local patch also makes `pangolin version` avoid its
separate update request. `pangolin update` prints this message and does not
download or execute an installer:

> This installation is managed by pacman. Run sudo pacman -Syu to update Pangolin.

CodeFriendly modified `cmd/update/update_unix.go` and `cmd/version/version.go`
on 2026-10-30 to use package-manager updates. The patch is included in the
source archive.
The package does not install or enable a service. Pangolin's service commands
remain explicit user actions. Tunnel operation can require root privileges.

## Licenses and corresponding source

The CLI uses AGPL-3.0-only under the upstream default grant. Newt and Olm also
carry AGPLv3 licenses. Original dependency notices retain their own terms.
The package installs the upstream license, dependency license and NOTICE
files, Unicode data terms, and the Go runtime license.

The pinned `go-licenses` tool checks the selected dependency licenses against
the reviewed allowlist before compilation. The recipe copies original license
and notice files from those modules, including nested files. It saves the
license report with the corresponding source. This gate does not replace a
source review or establish that all upstream attribution is complete.

Each build exports `pangolin-<version>-<release>.src.tar.zst` beside the binary.
Publish this source archive with the binary. It includes the patched source,
vendored dependencies, a local Go module download mirror, generated notices,
the original release archive, and packaging files. Compiler caches and built
executables are excluded. Dependency source retains its original licenses.

To rebuild from the source archive on Arch Linux, extract it into an empty
directory and run:

```bash
mkdir src
cp -a cli-0.19.1 src/
makepkg --noextract --clean --syncdeps --noconfirm
```

`--noextract` preserves the supplied dependencies and notices. Compilation and
tests use vendor mode with network dependency resolution disabled. Arch build
dependencies must already be available or installable through pacman.

## Updating the recipe

Update the source version and checksum. Review changed license terms and
dependency licenses. Regenerate `.SRCINFO`, then run the same Docker build.
Do not bypass a failed license check or an updater patch failure.
Validate each advertised architecture before publication. A working CLI and
unit tests do not prove a real tunnel works with a particular server.
