# cliamp source package

cliamp's original application is MIT-licensed. This executable statically links
go-librespot v0.9.1, whose grant permits GPL version 3 or later; the combined work
is distributed under GPL-3.0-or-later. Original application and dependency terms
remain in `/usr/share/licenses/cliamp/`, including the GPL text, exact nested
dependency notices, Go runtime license and Unicode terms.

## Packaging changes (13 November 2026)

`licensed-vorbis.patch` changes only go.mod and go.sum, pinning vorbis-go to
`7a1a42804d4d9f8eb7466be0b953c18069c6c271`
(`v0.0.0-20261030222311-7a1a42804d4d`). Its parent is the original
`b5b85f1ec645f3cffd000583b7c7f60b45d95379`; the sole upstream change is the
addition of the owner's MIT LICENSE, not implementation or dependency changes.
The later go.mod addition is deliberately not used. Original generated headers
are unchanged; the owner's grant is installed separately.
See https://github.com/xlab/vorbis-go/issues/12#issuecomment-6534813433.

The segmentio/asm v1.2.1 module archive omits its upstream MIT-0 notice. The recipe
retrieves the exact tag's checksummed LICENSE. go-licenses v2.0.1 cannot classify
MIT-0, so only this exact module version and Go checksum receive an explicit
manual MIT-0 classification, recorded in the installed CSV. Its original notice
is installed unchanged. Every other unknown or non-allowlisted license fails
the pinned go-licenses v2.0.1 gate.
Assembly and C dependency discovery is outside that tool's automatic coverage;
the supplied nested notices and bundled Vorbis/Ogg header notices are retained.
No audio, provider or UI functionality is removed.

## Corresponding source and offline rebuild

Distribute `cliamp-2.4.1-1.src.tar.zst` next to the binary package, with equivalent
access and a clear source link. It contains the patched application, all vendored
Go dependencies (including test imports), original source archives, original
notices, recipe and patch. No executable, Go build cache or credentials are included.
Use the packaging files from this archive, not an unrelated current checkout.

With Arch base-devel, Go, git and the recipe's runtime dependencies installed,
unpack the source archive into a writable directory. Create `src/`, move
`cliamp-2.4.1/` into it, and extract `vorbis-go-7a1a428.tar.gz` inside `src/`.
Copy `Unicode-LICENSE.txt` into `src/`. Then, as a non-root user:

```sh
makepkg --noextract --noprepare --noconfirm
```

The already prepared source contains the reviewed notices and vendor tree.
`build()` and `check()` use that tree with GOPROXY=off and GOSUMDB=off; they run
without network access. `prepare()` performs the online, locked module download,
checksum verification, license gate and vendoring only for a fresh source build.
The Go version used for the binary is recorded in its `.BUILDINFO`.
