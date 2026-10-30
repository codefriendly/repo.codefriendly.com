#!/usr/bin/env python3
"""Render the Arch package listings, or check an explicit publication target."""

import argparse
import html
from pathlib import Path
import re
import sys
import tomllib

ROOT = Path(__file__).resolve().parent.parent
ARCH = ROOT / "packages" / "arch"
SOURCE = "https://github.com/codefriendly/repo.codefriendly.com/tree/main/packages/arch"
SERVER = "https://repo.codefriendly.com/arch"


def manifest():
    records = tomllib.loads((ARCH / "manifest.toml").read_text())
    for name, record in records.items():
        if not isinstance(record, dict):
            raise ValueError(f"{name}: expected a package table")
        if name in {".", ".."} or not re.fullmatch(r"[A-Za-z0-9@_+][A-Za-z0-9@._+-]*", name):
            raise ValueError(f"Invalid package name: {name}")
        if not (ARCH / name / "PKGBUILD").is_file():
            raise ValueError(f"Missing recipe for {name}")
        for target in ("binary_repo", "aur_maintainer"):
            if type(record.get(target)) is not bool:
                raise ValueError(f"{name}: {target} must be an explicit boolean")
        if record["binary_repo"]:
            for key in ("published_version", "architecture"):
                if not re.fullmatch(r"[A-Za-z0-9._+~-]+", record.get(key, "")):
                    raise ValueError(f"{name}: missing or invalid {key}")
        for flag in ("debug_package", "source_archive"):
            if type(record.get(flag, False)) is not bool:
                raise ValueError(f"{name}: {flag} must be boolean")
    return records


def upstream(name):
    # Read metadata without executing the PKGBUILD.
    for line in (ARCH / name / ".SRCINFO").read_text().splitlines():
        if line.strip().startswith("url = "):
            return line.strip().removeprefix("url = ")
    raise ValueError(f"Missing upstream URL for {name}")


def binary_catalog(records):
    rows = []
    for name, record in sorted(records.items()):
        if not record["binary_repo"]:
            continue
        version = html.escape(record["published_version"])
        architecture = record["architecture"]
        names = [name, name + "-debug"] if record.get("debug_package") else [name]
        source_link = ""
        if record.get("source_archive", False):
            source_link = f' · <a href="{SERVER}/sources/{name}-{record["published_version"]}.src.tar.zst">Source archive</a>'
        for package in names:
            description = record.get("description", "") if package == name else f"Debugging symbols for {name}."
            artifact = f"{SERVER}/{architecture}/{package}-{record['published_version']}-{architecture}.pkg.tar.zst"
            rows.append(f'''            <div class="package">
              <div class="package-heading">
                <a href="{html.escape(artifact)}">{html.escape(package)}</a>
                <span class="version">{version}</span>
              </div>
              <p>{html.escape(description)}</p>
              <small><a href="{html.escape(artifact)}.sig">Signature</a>{source_link}</small>
            </div>''')
        rows.append(f'''            <p class="package-links"><a href="{SOURCE}/{name}">Packaging source</a> · <a href="{html.escape(upstream(name))}">Upstream project</a></p>''')
    return "\n".join(rows)


def aur_catalog(records):
    rows = []
    for name, record in sorted(records.items()):
        if not record["aur_maintainer"]:
            continue
        rows.append(f'''            <div class="package">
              <div class="package-heading"><a href="https://aur.archlinux.org/packages/{name}">{html.escape(name)}</a></div>
              <p>{html.escape(record.get('description', ''))}</p>
              <p class="note">Maintained by CodeFriendly on AUR. Build locally; no binary hosted here.</p>
              <small><a href="{SOURCE}/{name}">Packaging source</a> · <a href="{html.escape(upstream(name))}">Upstream project</a></small>
              <div class="command" data-copy-label="{html.escape(name)} AUR installation command"><pre><code>paru -S {html.escape(name)}</code></pre></div>
              <p class="note">Requires the paru AUR helper. Review the recipe before building, or <a href="https://wiki.archlinux.org/title/Arch_User_Repository#Installing_and_upgrading_packages">build manually</a>.</p>
              <p class="note">{html.escape(record.get('reason', ''))}</p>
            </div>''')
    return "\n".join(rows)


def readme_catalog(records):
    rows = ["| Package | Install method | Command |", "| --- | --- | --- |"]
    for name, record in sorted(records.items()):
        source = f"[{name}](packages/arch/{name})"
        if record["binary_repo"]:
            rows.append(f"| {source} | Signed binary repository | `sudo pacman -S {name}` |")
        if record["aur_maintainer"]:
            rows.append(f"| {source} | [AUR — build locally](https://aur.archlinux.org/packages/{name}) | `paru -S {name}` |")
    return "\n".join(rows)


def replace_block(text, marker, content):
    start, end = f"<!-- {marker}:start -->", f"<!-- {marker}:end -->"
    pattern = re.compile(re.escape(start) + r"[\s\S]*?" + re.escape(end))
    if len(pattern.findall(text)) != 1:
        raise ValueError(f"Expected exactly one {marker} block")
    return pattern.sub(lambda _: f"{start}\n{content}\n{end}", text)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--check", action="store_true", help="Check generated listings without changing files")
    action.add_argument("--allow-aur", metavar="PKGBASE", help="Exit successfully only for an approved AUR maintainer target")
    action.add_argument("--allow-binary", metavar="PKGBASE", help="Exit successfully only for an approved binary target")
    args = parser.parse_args()
    records = manifest()
    for name, target in ((args.allow_aur, "aur_maintainer"), (args.allow_binary, "binary_repo")):
        if name is not None:
            if records.get(name, {}).get(target) is not True:
                print(f"Refusing {target} publication for {name}: not opted in by packages/arch/manifest.toml", file=sys.stderr)
                return 1
            return 0
    page = ROOT / "site" / "index.html"
    readme = ROOT / "README.md"
    original_page = page.read_text()
    rendered_page = replace_block(original_page, "binary-catalog", binary_catalog(records))
    rendered_page = replace_block(rendered_page, "aur-catalog", aur_catalog(records))
    original_readme = readme.read_text()
    rendered_readme = replace_block(original_readme, "package-catalog", readme_catalog(records))
    stale = False
    for path, old, new in ((page, original_page, rendered_page), (readme, original_readme, rendered_readme)):
        if old != new:
            if args.check:
                print(f"Out-of-date catalog: {path.relative_to(ROOT)}", file=sys.stderr)
                stale = True
            else:
                path.write_text(new)
                print(f"Updated {path.relative_to(ROOT)}")
    return int(stale)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, tomllib.TOMLDecodeError) as error:
        print(error, file=sys.stderr)
        sys.exit(1)
