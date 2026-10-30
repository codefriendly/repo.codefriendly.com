# Monstar package license notes

Monstar is MIT-licensed. Its license is installed beside this file as `LICENSE`.
This package also includes the following code and data:

- Ghostty at `9ed61428daa9f15b2dc89e73f9fe0d16d3a6bb71`: `Ghostty-LICENSE`.
- Ghostty's embedded X11 color table: `Xorg-RGB-COPYING`, from X.Org rgb 1.1.0.
- zig-wayland at `a8e10e87e5ebb49ce518ac3d2198909c87ee615a`: `zig-wayland-LICENSE`.
- uucode at `2826a37a4562284fdacd8fa029d49509cc9bffcd`: `uucode-LICENSE.md`,
  `uucode-LICENSE_unicode`, and `uucode-LICENSE_Bjoern_Hoehrmann`.
  The Hoehrmann notice also covers Ghostty's UTF-8 decoder.
- Highway at `66486a10623fa0d72fe91260f96c892e41aceb06`:
  `highway-LICENSE-BSD3` (the BSD license option).
- Ghostty's vendored simdutf 9.0.0: `simdutf-LICENSE-MIT`,
  `simdutf-LICENSE-APACHE`, and `simdutf-third-party-notices.h`.
  The full header retains the derived-code notices and modification statements.
- z2d at `47fc1030c1636dcfb75ea1cc238f706dd1feb379`: `z2d-LICENSE` and
  `z2d-COPYING`. These include the notices for its derived code.
- The embedded Nerd Font symbols: `SymbolsNerdFontMono-LICENSE`.
- Vendored stb code: `stb_image.h-LICENSE` and `stb_image_resize.h-LICENSE`.
- Zig standard-library and runtime code: `Zig-LICENSE`, `libcxx-LICENSE.TXT`,
  `libcxxabi-LICENSE.TXT`, and `libunwind-LICENSE.TXT`.
- The iTerm2-Color-Schemes collection at
  `8c97c3c684da58a19149d1080f3d18ff5e161c01`:
  `iterm2-Color-Schemes-LICENSE`. Individual themes retain their authors' rights.

## z2d source

z2d is covered by MPL-2.0. The exact source used for this package is installed
under `/usr/share/doc/monstar/z2d-source/`, with its build files and notices.
No local changes are made to that source. The upstream repository is
<https://github.com/vancluever/z2d/tree/47fc1030c1636dcfb75ea1cc238f706dd1feb379>.

The source form retains the notices for derived Cairo, Pixman, tiny-skia, and
W3C code. The full upstream license file also describes test-only components;
this package does not install z2d's test fonts.

These component licenses do not relicense Monstar as a whole. System libraries
are supplied by separate Arch packages. The official Zig 0.16.0 compiler is used
as a build tool. The compiler itself is not installed by this package.
