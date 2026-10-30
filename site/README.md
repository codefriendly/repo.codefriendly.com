# Repository website

This is a small Jinja-based static site. The ignored `dist/` directory contains the complete deployable website: `index.html`, `packages.html`, `assets/site.css` and `assets/copy.js`. The home page contains repository setup and signing details. The Packages page contains separate repository and AUR catalogs. Both pages have top anchor navigation. The server needs no Python, Node.js, PHP or template engine.

## Build and preview

Use Python 3.11+, uv, Node.js 20+ and npm. From the repository root:

```bash
npm --prefix site ci --ignore-scripts
npm --prefix site run build
npm --prefix site run check
python -m http.server 8080 --bind 127.0.0.1 --directory site/dist
```

Open http://127.0.0.1:8080/. For CSS development, run `npm --prefix site run watch` in another terminal. Package and public-key links point to the published HTTPS files. Font loading uses Google Fonts; system fonts are the offline fallback.

`build` cleans `dist/`, renders both pages and the root README table, compiles Tailwind, and copies source assets. It does not sign or publish anything. `check` requires a build first. It compares the generated pages, README table, CSS and copied JavaScript against their sources without writing files. Missing or stale output causes a nonzero exit status.

In CI, install the supported runtimes and uv, run `npm --prefix site ci --ignore-scripts`, then run the build, check and `bash scripts/tests/packaging.sh`. Verify that the tracked README table has no diff. Upload only `site/dist/` as the website artifact. No generated HTML or CSS is committed.

Jinja and its dependency are pinned in `scripts/catalog.py.lock`. The build uses uv's isolated script environment, not a global Python installation. Python packages are not installed in the website directory. The existing `python3 scripts/catalog.py --allow-binary <pkgbase>` and `--allow-aur` publication gates remain standard-library-only.

## Source files

- `packages/arch/manifest.toml`: package descriptions, publication targets, latest released versions, publication timestamps and source-archive availability. This is the catalog's source of truth. The sidebar shows the five packages with the newest `published_at` timestamps, one entry per package. It uses each package's `published_version` and links to its catalog anchor. No release history is kept. The list is hidden when no binary package has a timestamp.
- `packages/arch/<pkgbase>/.SRCINFO`: upstream project URLs. The generator reads this metadata without executing recipes.
- `templates/base.html.j2`: shared head, top anchor navigation, footer and asset references.
- `templates/index.html.j2`: setup guide and signing details.
- `templates/packages.html.j2`: repository and AUR sections, with package loops.
- `styles.css` and `theme.css`: shared styling and brand tokens.
- `assets/copy.js`: optional clipboard behavior shared by both pages.

Edit these sources, then run `npm --prefix site run build`. Do not edit or commit `dist/`. The generated root README table remains tracked. Jinja escapes package text and fails on undefined template variables. No template rendering or JavaScript is required to read the deployed pages.

## Theme and styling

- `theme.css` defines only the shared brand colors and font families. The default Tailwind color palette is disabled so colors come from named `brand-*` tokens.
- `styles.css` uses Tailwind's standard spacing, type sizes, containers, and `sm`/`md`/`lg` breakpoints. Prefer ordinary whole-number utilities; do not add fractional nudges or custom layout tokens to chase exact pixels. Keep colors and fonts in the shared theme.
- `dist/assets/site.css` is the compiled, minified output. Build before preview or deployment. Do not edit it by hand.
- The two Tailwind development dependencies are pinned in `package.json` and `package-lock.json`.

To check reproducibility, save checksums for the files in `dist/`, rebuild, and compare the checksums. Unchanged input should produce identical output.

## Implementation requirements

- Preserve the CodeFriendly theme: Manrope for interface text and Geist Mono for commands and identifiers, with the declared system fallbacks.
- Preserve the semantic heading structure, skip link, visible keyboard focus, live clipboard feedback, and reduced-motion handling.
- Keep long commands and fingerprints horizontally scrollable without page-level overflow. Reserve space below command text so overlay scrollbars cannot cover it.
- Keep selection visible on both surfaces: ordinary text uses ink/canvas; dark code blocks use light-teal selection with ink text.
- Instructions and downloads must remain usable without JavaScript. Copy icons are an optional enhancement with accessible labels and status feedback; handle denied clipboard permission without losing access to the text. Give each shell command its own button; mark independent command lines with `data-copy-mode="lines"`. Keep configuration snippets together as one copyable block.
- Check desktop and mobile layouts after changes. Keep the deployed site static.

## Content maintenance

- After a package release, update its entry in `packages/arch/manifest.toml`, then run `npm --prefix site run build` and `npm --prefix site run check`. Do not add package rows by hand. For HTML/README generation alone, use `uv run --locked scripts/catalog.py`; add `--check` to compare without writing files.
- After public verification, record the release with `python3 scripts/catalog.py --record-release pkgbase version-pkgrel` before building the site. This replaces the package's published version and timestamp in the manifest. Follow `MAINTAINING.md` for timestamp handling. This local command does not publish anything. Do not infer release dates from Git commits or builds.
- Keep package versions and download URLs synchronized with the published repository, not simply the packaging source tree.
- Separate ready-to-install binaries from AUR/self-build recipes. Sononym is AUR-only; no Sononym or debug binaries are hosted.
- Keep every Arch-specific instruction, artifact link, and signing-key reference inside the Arch Linux section.
- Check the public-key fingerprint, expiry, package signatures, and database signature policy whenever signing configuration changes.
- Keep verification separate from commands that grant trust. Never suggest partial upgrades or disabling signatures.
- Preserve the full repository in `/arch/x86_64/`; the landing page does not generate package databases.

## Publication

Publication requires explicit owner confirmation. Run a successful build and check first, then deploy only the contents of `dist/` to their matching paths in the configured web document root. Publish assets before the HTML that links to them. Increment the stylesheet URL's `v` parameter in `templates/base.html.j2` when changing CSS, then rebuild. Never synchronize `site/` itself. Back up existing deployed files outside the web document root before replacing them. Do not use a root-level delete sync: `/arch/` contains separately published artifacts. Check both pages and all three top navigation anchors after deployment.
