# Maintaining the package monorepo

## Repository model

This monorepo keeps packaging sources in `packages/<format>/`. Arch packaging
lives in `packages/arch/<pkgbase>/`; shared tooling lives in `scripts/` and the
repository website in `site/`. Other format directories are added only when
actual packaging exists. Packages need not be published to the AUR.
For new imports, preserve standalone history only for packages we maintain in
the AUR. Import other packages as current files without their Git history.
Keep original attribution and license notices in both cases. The AUR stores
one Git repository per `pkgbase`.

The directories are ordinary tracked files, not nested repositories or Git
submodules. Subtree import commits connect the original package history to the
monorepo; `git subtree split` reconstructs a package-only history for
publication.

## Requirements

- Git with `git subtree`
- Python 3.11+ for the publication manifest and generated catalogs
- `makepkg`
- an SSH key registered with the AUR for publication
- AUR maintainership or co-maintainership for packages being published

## Adopting a package from the AUR

Adoption requires all three steps: import the package files, review packaging
security, and configure or verify upstream version tracking. Running
`scripts/adopt` alone completes only the import step; it does not complete the
adoption workflow.

### 1. Choose whether to preserve history

First ask the owner whether we maintain the package in AUR. The script asks
this question when neither maintainership flag is supplied:

```bash
scripts/adopt --dry-run pkgbase
scripts/adopt pkgbase
```

For automation, specify the answer explicitly:

```bash
scripts/adopt --no-aur-maintainer pkgbase
scripts/adopt --aur-maintainer pkgbase
```

- `--no-aur-maintainer` copies the current tracked files into
  `packages/arch/<pkgbase>/`. It does not import upstream commits, stage files,
  or create a commit. Review the files before committing them.
- `--aur-maintainer` imports the complete history through `git subtree`.
  It creates a commit and checks that the AUR tip remains in the split history.
  Obtain approval for that commit before running this mode.

Both modes read `https://aur.archlinux.org/<pkgbase>.git` and check its basic
metadata. Both require an existing commit, a clean worktree, and an unused
target directory. `--dry-run` reports the selected mode without changing files
or history. Unattended calls must supply a maintainership flag.

The answer selects the import mode only. It does not update the publication
manifest or authorize an AUR push.

### 2. Review packaging security (required)

For every adoption, review the imported `PKGBUILD` and all package-supplied
scripts, hooks, patches, and desktop launchers. This step is required even if
no build or `makepkg` command is planned. Adoption is incomplete until the
review findings and limitations have been reported.

Also complete this review before running `makepkg`, including `--printsrcinfo`:
loading a `PKGBUILD` executes its top-level shell code.

- Check source origins, transport security, checksum/signature verification,
  and whether sources are pinned or mutable.
- Inspect top-level code and build/package functions for unexpected commands,
  downloads, execution of downloaded code, privilege escalation, destructive
  operations, and writes outside the build/package directories.
- Inspect installation hooks and runtime launchers for unsafe quoting,
  permissions, credential access, and unexpected network or system changes.
- Report findings, trust assumptions, and anything not inspected. A packaging
  review does not establish that upstream source code or binaries are safe.
  Stop before executing suspicious code and ask how to proceed.

### 3. Verify upstream version tracking (required)

Check whether `packages/arch/.nvchecker.toml` covers the adopted package:

1. Compare the imported `PKGBUILD` version with the latest upstream version,
   using the official homepage or source URL from `PKGBUILD`.
2. Add a reliable `packages/arch/.nvchecker.toml` entry if coverage is missing. Match the
   package's release channel (stable, beta, or rolling) and version format.
   If an existing check covers it, document which entry applies. If no reliable
   check is available, report the limitation.
3. From the repository root, validate the check with
   `uvx nvchecker -c packages/arch/.nvchecker.toml` (or the installed `nvchecker`).
4. Report the packaged version, latest upstream version, and update status.
   Keep package updates separate from adoption; do not build or update the
   package merely to import it.

Here, “adopt” means importing a package. It does not claim the package or
grant maintainership on the AUR website.

## Importing an existing local repository

Ask the same maintainership question for a local standalone repository.
For packages we do not maintain in AUR, copy its current tracked files without
its `.git` directory. Preserve attribution and license notices.

For packages we maintain in AUR, import the repository history directly:

```bash
git subtree add \
  --prefix=packages/arch/pkgbase \
  /path/to/local-package-repository \
  master
```

Do not use `--squash`; retaining the complete history allows subsequent splits
to remain fast-forward updates of the AUR repository.

Verify the relationship after importing:

```bash
split=$(git subtree split --prefix=packages/arch/pkgbase)
git fetch \
  https://aur.archlinux.org/pkgbase.git \
  master:refs/remotes/aur/pkgbase
git merge-base --is-ancestor refs/remotes/aur/pkgbase "$split"
```

A zero exit status from `git merge-base --is-ancestor` confirms the relationship.

## Pulling updates from another package repository

For packages we maintain in AUR, pull later standalone commits into the existing
subtree:

```bash
git subtree pull \
  --prefix=packages/arch/pkgbase \
  /path/to/local-package-repository \
  master
```

This was used to import the later Feather Wallet Trezor compatibility patch
without rewriting package history.

## Updating a package

Make changes inside only the relevant package directory, then regenerate
`.SRCINFO`:

```bash
cd packages/arch/pkgbase
makepkg --printsrcinfo > .SRCINFO
cd ../../..
```

Review the package files and commit them in the monorepo. A commit touching
multiple package directories is split into each affected package history, so
package-specific commits are preferred.

### Converting a binary recipe to a source build

Check the AUR for a matching source recipe first. Review its files before using
it, and preserve attribution. Create a new `packages/arch/<name>/` directory for
the source recipe. Keep `packages/arch/<name>-bin/` unchanged while developing
and testing the source build. Do not rename the existing subtree or rewrite its
history to represent a different AUR package.

Build the source package in Docker. Check the package metadata, installed files,
license notices, corresponding-source requirements, and executable. Remove the
old `-bin` recipe only after these checks pass. Update upstream version tracking
and the local license inventory to use the source package name. Publication
approval remains separate. Commits and AUR history imports still require owner
authorization.

## Container builds

From the repository root, use the format-aware build command:

```bash
scripts/build arch cliamp
scripts/build arch cliamp --refresh-image --output /tmp/cliamp-build
```

The package name selects `packages/arch/<pkgbase>/`. Only `arch` is supported.
Other formats will use separate builders and images. Dockerfiles and container
entry scripts live in `docker/<format>/`.

Keep tools required by all Arch builds in `docker/arch/Dockerfile`. Update that
file when a new shared requirement is found. Keep package-specific build tools
in each recipe's `makedepends`, not in the shared image or host setup.

Docker must be installed and its daemon must be accessible to your user.
The command builds one shared local image, `codefriendly-build-arch:local`.
Docker caches its layers. Use `--refresh-image` at the start of a build session
to pull the current Arch base and rebuild all layers. Each build also upgrades
the whole disposable container before installing package dependencies.

Review the recipe and all helper files before building. The command copies the
complete package directory into a fresh container. It does not mount the host
checkout, credentials, output directory, or Docker socket. `makepkg` runs as an
unprivileged user with permission to run pacman through sudo inside the container.
Containers share the host kernel and are not a safe boundary for hostile recipes.

The container has a 2 GiB executable tmpfs at `/tmp` and 512 MiB of shared memory.
The tmpfs supports unnamed temporary files (`O_TMPFILE`) that the writable Docker
overlay can refuse. These limits do not reserve that amount of memory in advance.

The build installs dependencies from the standard Arch repositories by default.
Add `--codefriendly-repo` for packages that depend on our published binaries,
for example `scripts/build arch herdr-desktop --codefriendly-repo`.
This option downloads the public key, checks its pinned full fingerprint, and
enables the signed CodeFriendly repository only inside the disposable container.
Both package and database signatures remain required. It does not install AUR
dependencies, use the host's repository configuration, or bypass missing
dependencies. Builds use the Docker daemon's native architecture;
this is not a cross-compilation workflow.

The command prints the output path. By default it creates a directory under
`/tmp`; `--output` selects an empty directory instead. Outputs include packages,
generated `.SRCINFO`, and image/build logs. Each package also has a `.PKGINFO`
report, a `.files` inventory, a `.namcap.log` report, and a `.sha256` checksum.
Namcap findings are advisory; read its report before publication. A checked-in
`.SRCINFO` must match the recipe or the build stops before compiling.
Failed builds retain available logs and return a nonzero status.
The container is removed after the build. Debug
packages are disabled by default and removed from successful build outputs if a
recipe enables them. Source recipes and their `.SRCINFO` remain unchanged.
The command does not sign, publish, or change publication approval. It does not
prepare corresponding-source delivery or certify license compliance.

### Repeatable builds and CI

New recipes need an initial review of the sources, dependencies, licenses, and
installed files. Put repeatable checks in the recipe's `check()` function. Keep
license installation in `package()`. Use a locked dependency graph when upstream
provides one. Missing dependencies, failed tests, and license-policy failures must
return a nonzero status. Do not replace a failed check with an agent-only step.

After that review, a CI runner with Docker can use the same build command:

```bash
scripts/build arch strata-fm --output /tmp/strata-build
```

Retain the output directory as the CI artifact. Build and test jobs need no
signing keys, SSH credentials, or publication permission. Publication remains a
separate operation. No CI workflow or automatic publication is configured here.
Updates can reuse the reviewed checks. Changes to license terms or dependencies
outside the reviewed policy still require review.

Amp orbs can use the same command. Install Docker during orb setup and run its
daemon as a supervised orb service, as described in
[Customizing Orbs](https://ampcode.com/docs/orbs/customizing#installing-software).
Do not launch a background daemon from the setup script. No orb project settings
are required by the build command itself. Arch repositories are rolling, so the
Dockerfile alone does not provide exact historical rebuilds.

Run the container integration tests with an accessible Docker daemon:

```bash
bash scripts/tests/build.sh
```

Check Strata's license report renderer without Docker:

```bash
python3 scripts/tests/strata-licenses.py
```

## Publication targets

`packages/arch/manifest.toml` separates publication targets from recipe storage:

- `binary_repo = true`: approved for the signed binary repository.
- Approval does not imply publication. Omit `published_version` and `published_at`
  until the first release passes public verification. Unpublished packages do
  not appear in the generated binary catalog.
- `aur_maintainer = true`: owned/maintained by CodeFriendly on AUR.
- `source_archive = true`: link the matching `<pkgbase>-<published_version>.src.tar.zst`
  under `/arch/sources/`. Upload and verify it before publishing the binary.
- Unlisted recipes default to neither target. Importing does not grant permission
  to redistribute an application or claim its AUR maintainership.

Cliamp is currently a binary target. Sononym is maintained on AUR but is excluded
from binary publication because its bundled license prohibits redistribution
without written permission. Debug packages are not published.

Before staging a binary, require the manifest check to succeed:

```bash
python3 scripts/catalog.py --allow-binary pkgbase
```

After successful binary publication, verify the public artifacts and repository
installation. Then record the release. Do not record a build, staging upload or
failed publication as a release.
The command below only records local data; it does not upload or verify artifacts.

```bash
python3 scripts/catalog.py --record-release pkgbase version-pkgrel
npm --prefix site run build
npm --prefix site run check
```

The release command replaces `published_version` and `published_at` in the
package's manifest table. It requires binary approval. Repeating the command
for the same version preserves its timestamp. New versions replace the old
values; no release-history file is kept. Timestamps default to now in UTC.
If `PACKAGE-REVIEW.local.md` exists, release recording also refreshes its marked
publication table. Use `python3 scripts/catalog.py --sync-package-review` to
refresh that table separately. The optional local review holds publication
decisions and evidence. Generated publication data does not grant review approval.
Use `--published-at 2026-10-30T20:33:00Z` to supply a verified timestamp.
The home page shows five distinct packages sorted by their latest publication
timestamp, with package names in descending order to break exact timestamp ties.
Packages without a timestamp remain in the catalog but not in recent updates.
Older publication dates are not guessed from Git or local recipe versions.
For the initial backfill only, the owner approved 2026-10-30 as the
fallback date for Cliamp, Monstar and Strata. Their original publication dates
were not confirmed. The six initial packages use midnight UTC for unknown times;
this placeholder does not claim a known publication time.
There is no binary-upload script yet. A future publisher must run this command
only after its public verification succeeds. Recording a release does not deploy
the website; that action still needs explicit approval.

Manifest approval never replaces the owner's explicit confirmation for a public
action. Keep package signing keys outside build environments and web roots.

## Publishing to AUR

Preview the Git ref update:

```bash
scripts/publish --dry-run pkgbase
```

Publish over SSH:

```bash
scripts/publish pkgbase
```

The publishing script:

1. requires a clean worktree and committed package history;
2. requires `.SRCINFO` to exactly match `makepkg --printsrcinfo`;
3. fetches the current public AUR history;
4. verifies explicit AUR maintainership approval in the manifest;
5. splits only the selected package directory;
6. rejects a non-fast-forward update; and
7. pushes without `--force`.

Dry-run does not send objects or execute AUR receive hooks. Only a real push can
confirm SSH authorization and server-side validation.

## Prefix migrations and tooling checks

The owner-approved history reset replaced unmaintained package histories with
a snapshot. It preserved Sononym's package-only history because we maintain
that package in AUR. Other package files retain their attribution and notices.

For AUR-maintained packages, subtree commits contain `git-subtree-dir`,
`git-subtree-mainline`, and `git-subtree-split` trailers. Keep these continuity
records intact. Renaming a subtree directory does not retain split ancestry
automatically.

Before a future prefix migration, record the split for the old prefix. The move
commit must identify the new prefix, its pre-move monorepo parent as the mainline,
and that recorded split. Verify that splitting the new prefix returns the exact
same commit before accepting the migration. Never rewrite the package-only
history of an AUR-maintained package.

Run the local adoption/publication regression tests without contacting the AUR:

```bash
bash scripts/tests/packaging.sh
```

## Licensing

Repository tooling and documentation written by CodeFriendly are MIT-licensed.
Imported package histories and third-party material retain their own terms. See
[LICENSE](LICENSE) and [NOTICE.md](NOTICE.md).
