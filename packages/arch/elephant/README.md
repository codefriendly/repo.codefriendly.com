# Elephant source package

This split package builds Elephant, the data provider and executor behind the
Walker launcher, from a checksummed upstream release. One build produces:

- `elephant`: the `elephant` command and a systemd user unit.
- `elephant-<provider>`: one package per provider plugin, installed in
  `/usr/lib/elephant/`.
- `elephant-all`: a metapackage for the general-purpose providers. App- and
  compositor-specific providers (1password, bitwarden, protonpass, niriactions,
  nirisessions) are optional dependencies; install them individually.

Upstream's `aptpackages` and `dnfpackages` providers are not built.

Go plugins load only into the binary they were compiled with. Every provider
therefore depends on the exact `elephant` version and release, so pacman always
upgrades the set together. `check()` loads every plugin into the built binary.

## Usage

```bash
sudo pacman -S walker elephant-all
systemctl --user enable --now elephant.service
```

The package installs `/usr/lib/systemd/user/elephant.service`, so
`elephant service enable` is not needed. It would write a second unit to
`~/.config/systemd/user/`.

## Build

From the repository root:

```bash
scripts/build arch elephant --output /tmp/elephant-build
```

The build vendors the Go modules, checks dependency licenses with
`go-licenses`, and installs the license and dependency notices in every
package, because each plugin statically links Go dependencies. The SQLite C
source compiled in by `mattn/go-sqlite3` is in the public domain. The build also writes
`elephant-<version>-<release>.src.tar.zst`, the corresponding source for the
binary and every plugin, including the complete module downloads.
