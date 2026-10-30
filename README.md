# CodeFriendly package repository

Packaging sources, maintenance tools, and the website for the CodeFriendly
package repository at `repo.codefriendly.com`.

- `packages/arch/<pkgbase>/` — Arch Linux packaging sources.
- `packages/arch/.nvchecker.toml` — upstream version checks for Arch packages.
- `scripts/` — adoption, AUR publication, and local regression tests.
- `site/` — the static repository landing page.

Packages here are not necessarily published to the AUR or the binary repository.
Inclusion does not imply that CodeFriendly is the current AUR maintainer.

## Arch packages

<!-- package-catalog:start -->
| Package | Install method | Command |
| --- | --- | --- |
| [cliamp](packages/arch/cliamp) | Signed binary repository | `sudo pacman -S cliamp` |
| [herdr-core](packages/arch/herdr-core) | Signed binary repository | `sudo pacman -S herdr-core` |
| [monstar](packages/arch/monstar) | Signed binary repository | `sudo pacman -S monstar` |
| [pangolin](packages/arch/pangolin) | Signed binary repository | `sudo pacman -S pangolin` |
| [remanager](packages/arch/remanager) | Signed binary repository | `sudo pacman -S remanager` |
| [sononym](packages/arch/sononym) | [AUR — build locally](https://aur.archlinux.org/packages/sononym) | `paru -S sononym` |
| [strata-fm](packages/arch/strata-fm) | Signed binary repository | `sudo pacman -S strata-fm` |
<!-- package-catalog:end -->

Configure the [signed binary repository](https://repo.codefriendly.com/#arch)
before using its pacman command. AUR commands require an AUR helper such as
`paru` and build locally; review the recipe before building.

Only Sononym is currently maintained by CodeFriendly on AUR. Its vendor license
does not permit us to redistribute the application, so no Sononym binary is hosted.

Other directories under [`packages/arch/`](packages/arch/) are **recipe only**:
their publication targets have not been reviewed. Debug packages are not hosted.
Versions here may differ from those published in Arch repositories or the AUR.

Publication targets and released versions are recorded in
[`packages/arch/manifest.toml`](packages/arch/manifest.toml). Regenerate the site
and this table with `npm --prefix site run build`; check the generated HTML,
README table and CSS with `npm --prefix site run check`. See the
[website build instructions](site/README.md) for prerequisites and templates.

## Repository website

The Jinja templates and source assets live in [`site/`](site/README.md).
Build output goes into ignored `site/dist/` for preview and deployment.
The home page documents repository setup. The Packages page has separate
repository and AUR sections, with downloads, signatures and source links.
Page publication is separate from package publication and requires explicit approval.

## Contributing

See [MAINTAINING.md](MAINTAINING.md) for maintenance and publishing instructions.

## License

CodeFriendly-authored tooling and documentation are available under the
[MIT License](LICENSE). See [NOTICE.md](NOTICE.md) for third-party material.
