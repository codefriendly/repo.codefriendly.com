#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["jinja2==3.1.6"]
# ///
"""Render the static website and README, or check a publication target."""

import argparse
from datetime import date
import json
from pathlib import Path
import re
import sys
import tomllib

ROOT = Path(__file__).resolve().parent.parent
ARCH = ROOT / "packages" / "arch"
SOURCE = "https://github.com/codefriendly/repo.codefriendly.com/tree/main/packages/arch"
SERVER = "https://repo.codefriendly.com/arch"


def releases():
    entries = json.loads((ARCH / "releases.json").read_text())
    seen = set()
    for entry in entries:
        date.fromisoformat(entry["date"])
        key = (entry["name"], entry["version"])
        if key in seen or not re.fullmatch(r"[A-Za-z0-9._+~-]+", entry["version"]):
            raise ValueError(f"Duplicate or invalid release: {key}")
        seen.add(key)
    return entries


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


def site_pages(records):
    from jinja2 import Environment, FileSystemLoader, StrictUndefined

    environment = Environment(
        loader=FileSystemLoader(ROOT / "site" / "templates"),
        autoescape=True,
        undefined=StrictUndefined,
        keep_trailing_newline=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    binary_packages, aur_packages = [], []
    for name, record in sorted(records.items()):
        if not (record["binary_repo"] or record["aur_maintainer"]):
            continue
        package = {
            "name": name,
            "description": record.get("description", ""),
            "packaging_source": f"{SOURCE}/{name}",
            "upstream": upstream(name),
            "reason": record.get("reason", ""),
        }
        if record["aur_maintainer"]:
            aur_packages.append(package)
        if record["binary_repo"]:
            version, architecture = record["published_version"], record["architecture"]
            names = [name, name + "-debug"] if record.get("debug_package") else [name]
            for binary in names:
                binary_packages.append({
                    **package,
                    "name": binary,
                    "version": version,
                    "description": package["description"] if binary == name else f"Debugging symbols for {name}.",
                    "download": f"{SERVER}/{architecture}/{binary}-{version}-{architecture}.pkg.tar.zst",
                    "source_archive": f"{SERVER}/sources/{name}-{version}.src.tar.zst" if record.get("source_archive") else None,
                })
    recent = sorted(
        (entry for entry in reversed(releases()) if records.get(entry["name"], {}).get("binary_repo")),
        key=lambda entry: entry["date"], reverse=True,
    )[:5]
    return {
        ROOT / "site" / "dist" / name: environment.get_template(name + ".j2").render(
            binary_packages=binary_packages, aur_packages=aur_packages, recent_releases=recent,
        )
        for name in ("index.html", "packages.html")
    }


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
    action.add_argument("--check", action="store_true", help="Check generated pages and README without changing files")
    action.add_argument("--allow-aur", metavar="PKGBASE", help="Exit successfully only for an approved AUR maintainer target")
    action.add_argument("--allow-binary", metavar="PKGBASE", help="Exit successfully only for an approved binary target")
    action.add_argument("--record-release", nargs=2, metavar=("PKGBASE", "VERSION"), help="Record a verified binary publication; does not publish or render")
    parser.add_argument("--released-on", type=date.fromisoformat, help="Publication date (YYYY-MM-DD); defaults to today")
    args = parser.parse_args()
    if args.released_on and not args.record_release:
        parser.error("--released-on requires --record-release")
    records = manifest()
    if args.record_release:
        name, version = args.record_release
        record = records.get(name, {})
        if not record.get("binary_repo") or record.get("published_version") != version:
            raise ValueError("Release must match an approved package's published_version")
        released_on = args.released_on or date.today()
        if released_on > date.today():
            raise ValueError("Publication date cannot be in the future")
        entries = releases()
        if not any(entry["name"] == name and entry["version"] == version for entry in entries):
            entries.append({"name": name, "version": version, "date": released_on.isoformat()})
            (ARCH / "releases.json").write_text(json.dumps(entries, indent=2) + "\n")
        return 0
    for name, target in ((args.allow_aur, "aur_maintainer"), (args.allow_binary, "binary_repo")):
        if name is not None:
            if records.get(name, {}).get(target) is not True:
                print(f"Refusing {target} publication for {name}: not opted in by packages/arch/manifest.toml", file=sys.stderr)
                return 1
            return 0
    readme = ROOT / "README.md"
    rendered = site_pages(records)
    rendered[readme] = replace_block(readme.read_text(), "package-catalog", readme_catalog(records))
    stale = False
    for path, new in rendered.items():
        old = path.read_text() if path.exists() else None
        if old != new:
            if args.check:
                print(f"Out-of-date generated file: {path.relative_to(ROOT)}", file=sys.stderr)
                stale = True
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(new)
                print(f"Updated {path.relative_to(ROOT)}")
    return int(stale)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, tomllib.TOMLDecodeError) as error:
        print(error, file=sys.stderr)
        sys.exit(1)
