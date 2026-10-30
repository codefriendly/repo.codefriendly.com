#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 CodeFriendly
# SPDX-License-Identifier: MIT
"""Collect notices from the locked Linux dependency graph and native sources."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile


def notices(root, destination):
    files = sorted(
        path for path in root.rglob("*")
        if path.is_file() and not path.is_symlink()
        and path.name.lower().startswith(("license", "licence", "copying", "copyright", "notice"))
    )
    if not files:
        raise SystemExit(f"No license notices found in {root}")
    for path in files:
        target = destination / path.relative_to(root)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)


out = Path(sys.argv[1])
out.mkdir(parents=True, exist_ok=True)
metadata = json.loads(subprocess.check_output([
    "cargo", "metadata", "--frozen", "--format-version=1",
    "--filter-platform", "x86_64-unknown-linux-gnu",
]))
resolved = {node["id"] for node in metadata["resolve"]["nodes"]}
# New license expressions require a new review. OR expressions select a
# permissive branch; retain all supplied texts so attribution is not lost.
reviewed = {
    "MIT", "Apache-2.0", "MIT OR Apache-2.0", "Apache-2.0 OR MIT",
    "BSD-3-Clause", "Unicode-3.0", "Zlib", "MIT OR Zlib OR Apache-2.0",
    "Apache-2.0 WITH LLVM-exception OR Apache-2.0 OR MIT",
    "Unlicense OR MIT", "MIT/Apache-2.0", "0BSD OR MIT OR Apache-2.0",
    "MIT OR Apache-2.0 OR Zlib", "MIT OR Unlicense",
    "(MIT OR Apache-2.0) AND Unicode-3.0",
    "(MIT OR Apache-2.0) AND Unicode-DFS-2016", "MIT AND Unicode-DFS-2016",
    "0BSD", "0BSD OR Apache-2.0", "Apache-2.0 / MIT", "Apache-2.0/MIT",
    "Apache-2.0 OR BSL-1.0", "BSD-2-Clause OR Apache-2.0",
    "Zlib OR Apache-2.0 OR MIT", "WTFPL",
}
inventory = []
for package in sorted(metadata["packages"], key=lambda p: (p["name"], p["version"])):
    if package["id"] not in resolved:
        continue
    name = f'{package["name"]}-{package["version"]}'
    license = package["license"]
    if license not in reviewed:
        raise SystemExit(f"Unreviewed license: {name}: {license}")
    root = Path(package["manifest_path"]).parent
    # The first-party workspace crates use the repository's Apache license.
    if package["name"] in {"herdr", "ghostty-vt"} and package["source"] is None:
        continue
    fallback = None
    if package["name"] in {
        "ratatui", "ratatui-core", "ratatui-crossterm", "ratatui-termwiz", "ratatui-widgets"
    }:
        fallback = ("0a2a7c0363a4806b0cf05c1915bf7cdd438f756c", "ratatui-LICENSE")
    elif package["name"] == "vtparse":
        fallback = ("edeae72b5fc55c7fa4aa1d08bbefd08c5493f757", "vtparse-LICENSE")
    elif package["name"] == "wezterm-input-types":
        fallback = ("d5ca5509b95edc31291ba29bd1fcbf3f0b12c92d", "wezterm-input-types-LICENSE")
    if fallback:
        vcs = json.loads((root / ".cargo_vcs_info.json").read_text())
        if vcs["git"]["sha1"] != fallback[0] or license != "MIT":
            raise SystemExit(f"Review supplemental license for {name}")
        destination = out / "cargo" / name
        destination.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(Path(sys.argv[0]).parent / fallback[1], destination / "LICENSE")
    else:
        notices(root, out / "cargo" / name)
    inventory.append({"name": name, "license": license, "source": package["source"]})
(out / "cargo-inventory.json").write_text(json.dumps(inventory, indent=2) + "\n")

ghostty = Path("vendor/libghostty-vt")
notices(ghostty, out / "ghostty")
# These amalgamated files contain additional attribution and BSD terms.
for name in ("simdutf.h", "simdutf.cpp"):
    target = out / "simdutf" / name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ghostty / "pkg/simdutf/vendor" / name, target)
# Zig's content-addressed cache includes native and table-generation sources.
# Retain each fetched component's notices, including Unicode data notices.
cache = Path(os.environ["ZIG_GLOBAL_CACHE_DIR"]) / "p"
for component in sorted(cache.iterdir()):
    if component.is_dir():
        notices(component, out / "zig-dependencies" / component.name)
    elif component.name.endswith(".tar.gz"):
        # The themes archive is fetched by Ghostty's build configuration but
        # is not linked into libghostty-vt or installed by this CLI recipe.
        if component.name == "N-V-__8AAEFmBABuDGOKxAI6VMg41b9euMZ-z7HS9EcUdaor.tar.gz":
            continue
        count = 0
        with tarfile.open(component) as archive:
            for member in archive.getmembers():
                path = Path(member.name)
                if not member.isfile() or not path.name.lower().startswith(
                    ("license", "licence", "copying", "copyright", "notice")
                ):
                    continue
                if path.is_absolute() or ".." in path.parts:
                    raise SystemExit(f"Unsafe archive path: {path}")
                target = out / "zig-dependencies" / component.stem / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(archive.extractfile(member).read())
                count += 1
        if not count:
            raise SystemExit(f"No license notices found in {component}")

zig = Path(os.environ["ZIG"]).parent
shutil.copyfile(zig / "LICENSE", out / "Zig-LICENSE")
for runtime in ("libcxx", "libcxxabi", "libunwind"):
    shutil.copyfile(zig / "lib" / runtime / "LICENSE.TXT", out / f"{runtime}-LICENSE.TXT")
with (out / "rust-build.txt").open("wb") as stream:
    stream.write(subprocess.check_output(["rustc", "--version"]))
    for path in (
        "/usr/share/licenses/rust/COPYRIGHT-library.html.rustc",
        "/usr/lib/rustlib/src/rust/library/compiler-builtins/LICENSE.txt",
        "/usr/lib/rustlib/src/rust/library/compiler-builtins/libm/LICENSE.txt",
    ):
        stream.write(Path(path).read_bytes())
        stream.write(b"\n")
print(f"Collected notices for {len(inventory)} Cargo dependencies and native components")
