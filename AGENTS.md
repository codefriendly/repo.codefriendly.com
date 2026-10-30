# Repository guidance

If `AGENTS.local.md` exists in the repository root, read it for additional local
guidance. It is optional and must not be required to build or contribute.

This repository contains packaging sources under `packages/<format>/`.
Arch Linux packages live in `packages/arch/<pkgbase>/`. Keep package changes
scoped to the relevant package; add other format directories only when needed.

## Repository website

`site/templates/index.html.j2` contains repository setup. The packages template
contains the repository and AUR catalogs. Follow `site/README.md` for site changes.
Edit templates and source assets, not the ignored output in `site/dist/`.
The shared base template owns top navigation, anchor links and asset references.
Styling uses Tailwind with shared tokens in `site/theme.css`
and reusable components in `site/styles.css`; regenerate `site/dist/assets/site.css`
with `npm --prefix site run build`. Keep published package versions distinct from
local source versions. Keep Arch-specific content inside the Arch Linux section.
Build and check before deployment. Deploy only the contents of `site/dist/`,
not templates, build scripts, source CSS, dependencies or development docs.
Obtain explicit confirmation before any live website change.
Package data comes from `packages/arch/manifest.toml` and `.SRCINFO`.
After a verified binary publication, record its version and timestamp with
`python3 scripts/catalog.py --record-release <pkgbase> <version-pkgrel>`.
This updates the package's `published_version` and `published_at` in the manifest.
Never record a build or failed publication as a release. See `MAINTAINING.md`.
Run `npm --prefix site run build` to render both pages, update the README table
and compile CSS. Run `npm --prefix site run check` to detect stale output
without writing files. The build needs uv, Python 3.11+, Node.js 20+ and npm.

## Publication targets

`packages/arch/manifest.toml` is an opt-in allowlist, not an inventory of every
recipe. `binary_repo` permits binary publication; `aur_maintainer` records the
owner's AUR maintainership. Unlisted recipes are not approved for either target.
Check `python3 scripts/catalog.py --allow-binary <pkgbase>` before staging any
binary. AUR publication checks its target automatically. Respect redistribution
restrictions: Sononym is AUR-only unless written vendor permission is obtained.
Do not publish debug packages. `published_version` describes a released artifact,
not necessarily the latest local recipe. No AUR action is authorized merely by
a manifest entry.

## Checking for upstream updates

Run `uvx nvchecker -c packages/arch/.nvchecker.toml` first for routine Arch upstream checks. Its
configuration records the authoritative upstream endpoint for each package;
do not rediscover release sources with broad web searches. Compare the
reported versions with each package's `pkgver` in `PKGBUILD`.

If an Arch package is not configured in `packages/arch/.nvchecker.toml`, use a lightweight
read-only lookup against the official homepage or source URL from its
`PKGBUILD`, then add a reliable check to `packages/arch/.nvchecker.toml`. For checks that
must use parallel agents, give each package a unique output path and require
only the packaged version, latest stable version, update status, and official
source. Do not build packages or perform detailed packaging analysis until a
newer release is confirmed.

## Subtree continuity

Before importing a package, ask whether the owner maintains it in AUR.
Preserve full history only for AUR-maintained packages. Import other packages
as current tracked files without upstream Git history. Preserve attribution
and license notices. Use the matching `scripts/adopt` maintainership flag.
Do not rewrite existing published history without explicit approval.

Each AUR-maintained package must retain its package-only history through subtree
trailers for `packages/arch/<pkgbase>`. Do not squash or rewrite that history.
Before a prefix change, record the old split and preserve the continuity
metadata. Verify that the new prefix yields the identical split commit.
Run `bash scripts/tests/packaging.sh` after changes to adoption or publishing
scripts.

## Updating a package

1. Check the upstream project's official release page, repository, or package
   metadata for a newer version. Compare the current `pkgver`, source URLs,
   and checksums before making changes.
2. Do initial update work in an isolated temporary directory under `/tmp`.
   Copy the complete package directory, including patches, helper scripts, and
   `.SRCINFO`, so failed updates do not dirty the repository.
3. Update `PKGBUILD`, regenerate `.SRCINFO` with
   `makepkg --printsrcinfo > .SRCINFO`, and run a real test build before
   finalizing the update:

   ```bash
   makepkg --cleanbuild --clean --noconfirm
   ```

   Use `--nodeps` only when dependency installation is unnecessary or
   unavailable, and report that limitation. For architecture-specific
   packages, test the native architecture and validate the other architecture's
   source URL and checksum metadata.
4. Review the resulting diff, then apply only the intended changes to the
   repository package directory. Regenerate `.SRCINFO` there as well.
5. Before reporting completion, run `git diff --check`, verify that `.SRCINFO`
   matches `makepkg --printsrcinfo`, and confirm that only intended files are
   modified.

Do not commit or publish package changes unless explicitly requested. Follow
[`MAINTAINING.md`](MAINTAINING.md) for subtree history, adoption, and AUR
publishing procedures.
