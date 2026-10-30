# Repository landing page

`index.html` is the editable page for https://repo.codefriendly.com/. The site uses locally compiled Tailwind CSS and optional clipboard controls. The deployed site is static HTML/CSS; no Node runtime, framework, PHP, or Tailwind browser CDN is needed on the server.

## Build and preview

Use Node.js 20+ and npm. From the repository root:

```bash
npm --prefix site ci --ignore-scripts
npm --prefix site run build
python -m http.server 8080 --bind 127.0.0.1 --directory site
```

Open http://127.0.0.1:8080/. For CSS development, run `npm --prefix site run watch` in another terminal. Package and public-key links point to the published HTTPS files. Font loading uses Google Fonts; system fonts are the offline fallback.

## Theme and styling

- `theme.css` defines only the shared brand colors and font families. The default Tailwind color palette is disabled so colors come from named `brand-*` tokens.
- `styles.css` uses Tailwind's standard spacing, type sizes, containers, and `sm`/`md`/`lg` breakpoints. Prefer ordinary whole-number utilities; do not add fractional nudges or custom layout tokens to chase exact pixels. Keep colors and fonts in the shared theme.
- `assets/site.css` is the compiled, minified output. It is tracked so a checkout can be previewed and deployed without installing Node; regenerate it after source or catalog changes. Do not edit it by hand.
- The two Tailwind development dependencies are pinned in `package.json` and `package-lock.json`.

To check reproducibility after a fresh install, rebuild and review `git diff -- site/assets/site.css`. An unchanged input should produce no CSS diff.

## Implementation requirements

- Preserve the CodeFriendly theme: Manrope for interface text and Geist Mono for commands and identifiers, with the declared system fallbacks.
- Preserve the semantic heading structure, skip link, visible keyboard focus, live clipboard feedback, and reduced-motion handling.
- Keep long commands and fingerprints horizontally scrollable without page-level overflow. Reserve space below command text so overlay scrollbars cannot cover it.
- Keep selection visible on both surfaces: ordinary text uses ink/canvas; dark code blocks use light-teal selection with ink text.
- Instructions and downloads must remain usable without JavaScript. Copy icons are an optional enhancement with accessible labels and status feedback; handle denied clipboard permission without losing access to the text. Give each shell command its own button; mark independent command lines with `data-copy-mode="lines"`. Keep configuration snippets together as one copyable block.
- Check desktop and mobile layouts after changes. Keep the deployed site static.

## Content maintenance

- Package listings and the root README table come from `packages/arch/manifest.toml`. Run `python3 scripts/catalog.py` after changing publication targets or released versions; run `python3 scripts/catalog.py --check` during validation. Rebuild the CSS afterward.
- Keep package versions and download URLs synchronized with the published repository, not simply the packaging source tree.
- Separate ready-to-install binaries from AUR/self-build recipes. Sononym is AUR-only; no Sononym or debug binaries are hosted.
- Keep every Arch-specific instruction, artifact link, and signing-key reference inside the Arch Linux section.
- Check the public-key fingerprint, expiry, package signatures, and database signature policy whenever signing configuration changes.
- Keep verification separate from commands that grant trust. Never suggest partial upgrades or disabling signatures.
- Preserve the full repository in `/arch/x86_64/`; the landing page does not generate package databases.

## Publication

Publication requires explicit owner confirmation. Rebuild first, then deploy only `index.html` and `assets/site.css` to their matching paths in the configured web document root. Publish the stylesheet before the HTML that links to it. Increment the stylesheet URL's `v` query parameter when changing the CSS so browsers do not reuse a cached version. Never synchronize this entire directory: it also contains source CSS, development documentation, package-manager metadata, and local dependencies. Back up the current homepage and stylesheet outside the web document root before replacing them. Do not touch `/arch/` artifacts when updating the website.
