# Herdr desktop: Arch Linux source build

This package builds herdr-app v0.1.10 from revision
36725d47c89cd19345994363d6d9cdee5c42c80b. Ghostty VT is pinned to
291fd050b9e9c293c8adb6a140742649b7e42d3a. Cargo.lock pins the Rust graph.
Zig 0.16.0 builds the static VT library. The executable uses system glibc.

The recipe and desktop entry are adapted from Qingxu's herdr-app-bin AUR
package (Qingxu <me@linioi.com>). This is a source package, not that binary
package. Only x86_64 is tested and supported by this recipe.

## Runtime and updates

A Linux desktop session and a working Vulkan driver are required. Install
herdr-core >=0.1.11 separately through pacman. The published core 0.1.15-1
meets the app's minimum version. The executable is named `herdr-app`.

This build does not set HERDR_APP_RELEASE or run upstream installers.
Upstream source builds disable normal app and core update checks. Update
both local packages with pacman. The package changes the source-build
label in defaults/frame/settings/main.js to name pacman instead of Git
(CodeFriendly, 2026-10-30). Do not set HERDR_RELEASES_URL: upstream
uses it to enable a test update server, including on source builds.
The app can still install a missing core on request, or install a core on
a remote machine. Those upstream features are not package installation.

## Third-party code and assets

LICENSE and the complete upstream THIRD-PARTY-NOTICES are installed under
/usr/share/licenses/herdr-desktop. The aggregate notices include platforms
and build tools that are not linked into the Linux executable. They are
retained rather than removed. The package adds its actual Rust and Zig
runtime notices and the attribution below.

GPUI and GPUI-kit use Apache-2.0. QuickJS uses MIT. Ghostty VT and its
native libraries are statically linked. Upstream's native inventory covers
Ghostty, simdutf (including TH CPU detection), Highway, Wuffs, uucode,
Unicode and Zig. The complete simdutf header is also installed.

Geist and JetBrains Mono use OFL-1.1. Symbols Nerd Font uses MIT.
Pixelated MS Sans Serif uses CC-BY-SA-3.0. PxPlus IBM VGA is part of
The Ultimate Oldschool PC Font Pack by VileR:
https://int10h.org/oldschool-pc-fonts/ (CC-BY-SA-4.0).
This package does not modify the fonts. The Win98 assets ship on Linux
because build.rs recursively embeds defaults/mods, defaults/icons and
defaults/frame. Upstream font, icon and modification notices are retained.

The resolved Linux normal-dependency graph includes option-ext 0.2.0
(MPL-2.0), through dirs-sys. Its complete, unmodified source archive is
installed beside these notices as option-ext-0.2.0.crate. It can be opened
with tar. The all-platform notices also list dwrote (Windows only) and
cbindgen (a build tool); neither is Linux runtime code. Linux runtime
code also includes libbz2-rs-sys (bzip2-1.0.6) and webpki-roots
(CDLA-Permissive-2.0). Their full notices are in THIRD-PARTY-NOTICES.

Upstream modifies vendored GPUI, GPUI-kit, taffy, zed-xim, xim-ctext and
quickjs-jit-runtime. Changes are marked HERDR in the supplied sources.
This package retains those notices. Its only source-code change is the
update-settings label described above, marked with a CodeFriendly comment.
Keep the matching source archives, Cargo.lock, vendored sources and this
recipe for redistribution. No public release or AUR publication is
authorized by this recipe.
