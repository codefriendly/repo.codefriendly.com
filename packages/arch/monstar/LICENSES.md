# Monstar package license notes

Monstar is MIT-licensed. Its license is installed beside this file as `LICENSE`.
This package also includes the following code and data:

- Ghostty at `0fa3d577a5614150ff8e2c152de5fb9d5c6d2dec`: `Ghostty-LICENSE`.
- Ghostty's embedded X11 color table: `Xorg-RGB-COPYING`, from X.Org rgb 1.1.0.
- zig-wayland at `fc7672f661874aa2015fc19a87ebabce787cf1c7`: `zig-wayland-LICENSE`.
- uucode at `1fb73433bba5d93366c57f23ff2e9d7939746500`: `uucode-LICENSE.md`,
  `uucode-LICENSE_unicode`, and `uucode-LICENSE_Bjoern_Hoehrmann`.
  The Hoehrmann notice also covers Ghostty's UTF-8 decoder.
- Highway at `66486a10623fa0d72fe91260f96c892e41aceb06`:
  `highway-LICENSE-BSD3` (the BSD license option).
- Ghostty's vendored simdutf 9.0.0: `simdutf-LICENSE-MIT`,
  `simdutf-LICENSE-APACHE`, and `simdutf-third-party-notices.h`.
  The full header retains the derived-code notices and modification statements.
- z2d at `8787d71bac42d9aab00428ccb37a4fd453418761`: `z2d-LICENSE` and
  `z2d-COPYING`. These include the notices for its derived code.
- The embedded Nerd Font symbols: `SymbolsNerdFontMono-LICENSE`.
- Ghostty's vendored stb code: `stb_image.h-LICENSE` and
  `stb_image_resize.h-LICENSE`.
- Zig standard-library and runtime code: `Zig-LICENSE`, `libcxx-LICENSE.TXT`,
  `libcxxabi-LICENSE.TXT`, and `libunwind-LICENSE.TXT`.
- The iTerm2-Color-Schemes collection at
  `8c97c3c684da58a19149d1080f3d18ff5e161c01`:
  `iterm2-Color-Schemes-LICENSE`. Individual themes retain their authors' rights.

## z2d source

z2d is covered by MPL-2.0. The exact source used for this package is installed
under `/usr/share/doc/monstar/z2d-source/`, with its build files and notices.
No local changes are made to that source. The upstream repository is
<https://github.com/vancluever/z2d/tree/8787d71bac42d9aab00428ccb37a4fd453418761>.

The source form retains the notices for derived Cairo, Pixman, tiny-skia, and
W3C code. The full upstream license file also describes test-only components;
this package does not install z2d's test fonts.

These component licenses do not relicense Monstar as a whole. System libraries
are supplied by separate Arch packages. The official Zig 0.17.1 compiler is used
as a build tool. The compiler itself is not installed by this package.
