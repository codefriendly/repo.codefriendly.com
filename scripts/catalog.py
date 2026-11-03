#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["jinja2==3.1.6"]
# ///
"""Render the static website and README, or check a publication target."""

import argparse
from datetime import datetime, timezone
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
        if record["binary_repo"] and not re.fullmatch(r"[A-Za-z0-9._+~-]+", record.get("architecture", "")):
            raise ValueError(f"{name}: missing or invalid architecture")
        if "published_version" in record and not re.fullmatch(r"[A-Za-z0-9._+~-]+", record["published_version"]):
            raise ValueError(f"{name}: invalid published_version")
        for flag in ("debug_package", "source_archive", "local_build"):
            if type(record.get(flag, False)) is not bool:
                raise ValueError(f"{name}: {flag} must be boolean")
        if record.get("local_build") and (record["binary_repo"] or record["aur_maintainer"]):
            raise ValueError(f"{name}: local_build excludes binary_repo and aur_maintainer")
        if "install" in record:
            names = [package["name"] for package in srcinfo(name)[1]]
            if record["install"] not in names:
                raise ValueError(f"{name}: install must name one of its packages: {', '.join(names)}")
        if "published_at" in record:
            if "published_version" not in record:
                raise ValueError(f"{name}: published_at requires published_version")
            timestamp = record["published_at"]
            if not isinstance(timestamp, datetime) or timestamp.tzinfo is None:
                raise ValueError(f"{name}: published_at must be a timestamp with a timezone")
    return records


def srcinfo(name):
    """Read base metadata and each package's name, description and architectures.

    Reads .SRCINFO without executing the PKGBUILD. Package sections inherit
    pkgdesc and arch from the pkgbase section unless they override them.
    """
    base, packages, current = {}, [], None
    for line in (ARCH / name / ".SRCINFO").read_text().splitlines():
        key, separator, value = line.strip().partition(" = ")
        if not separator:
            continue
        if key == "pkgname":
            current = {"name": value}
            packages.append(current)
        elif key in {"url", "pkgdesc", "arch"}:
            target = base if current is None else current
            if key == "arch":
                target.setdefault("arch", []).append(value)
            else:
                target[key] = value
    if "url" not in base:
        raise ValueError(f"Missing upstream URL for {name}")
    if not packages:
        raise ValueError(f"Missing pkgname for {name}")
    for package in packages:
        package.setdefault("pkgdesc", base.get("pkgdesc", ""))
        package.setdefault("arch", base.get("arch", []))
    return base, packages


def upstream(name):
    return srcinfo(name)[0]["url"]


def install_name(name, record):
    """Return the package that install commands name; a split package may choose one."""
    return record.get("install", name)


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
    binary_packages, aur_packages, local_packages = [], [], []
    for name, record in sorted(records.items()):
        if not (record["binary_repo"] or record["aur_maintainer"] or record.get("local_build")):
            continue
        base, split = srcinfo(name)
        package = {
            "name": name,
            "install": install_name(name, record),
            "description": record.get("description", ""),
            "packaging_source": f"{SOURCE}/{name}",
            "upstream": base["url"],
            "reason": record.get("reason", ""),
            "split": None,
        }
        if record["aur_maintainer"]:
            aur_packages.append(package)
        if record.get("local_build"):
            local_packages.append(package)
        if record["binary_repo"] and "published_version" in record:
            version, architecture = record["published_version"], record["architecture"]
            source_archive = f"{SERVER}/sources/{name}-{version}.src.tar.zst" if record.get("source_archive") else None

            def download(binary, arch=architecture):
                # Architecture-independent packages keep -any in their file names
                # but are served from the repository's architecture directory.
                return f"{SERVER}/{architecture}/{binary}-{version}-{arch}.pkg.tar.zst"

            if len(split) > 1:
                # A split package is one card that lists every package it builds.
                binary_packages.append({
                    **package,
                    "version": version,
                    "download": None,
                    "source_archive": source_archive,
                    "split": [
                        {
                            "name": member["name"],
                            "description": member["pkgdesc"],
                            "download": download(member["name"], "any" if member["arch"] == ["any"] else architecture),
                        }
                        for member in split
                    ],
                })
                continue
            names = [name, name + "-debug"] if record.get("debug_package") else [name]
            for binary in names:
                binary_packages.append({
                    **package,
                    "name": binary,
                    "version": version,
                    "description": package["description"] if binary == name else f"Debugging symbols for {name}.",
                    "download": download(binary),
                    "source_archive": source_archive,
                })
    recent = [
        {"name": name, "version": record["published_version"], "date": record["published_at"].date().isoformat()}
        for name, record in sorted(
            ((name, record) for name, record in records.items() if record["binary_repo"] and "published_at" in record),
            key=lambda item: (item[1]["published_at"], item[0]), reverse=True,
        )[:5]
    ]
    return {
        ROOT / "site" / "dist" / name: environment.get_template(name + ".j2").render(
            binary_packages=binary_packages, aur_packages=aur_packages, local_packages=local_packages,
            recent_releases=recent,
        )
        for name in ("index.html", "packages.html")
    }


def readme_catalog(records):
    rows = ["| Package | Install method | Command |", "| --- | --- | --- |"]
    for name, record in sorted(records.items()):
        source = f"[{name}](packages/arch/{name})"
        if record["binary_repo"] and "published_version" in record:
            count = len(srcinfo(name)[1])
            method = f"Signed binary repository ({count} split packages)" if count > 1 else "Signed binary repository"
            rows.append(f"| {source} | {method} | `sudo pacman -S {install_name(name, record)}` |")
        if record["aur_maintainer"]:
            rows.append(f"| {source} | [AUR — build locally](https://aur.archlinux.org/packages/{name}) | `paru -S {name}` |")
        if record.get("local_build"):
            rows.append(f"| {source} | [Recipe — build locally](https://repo.codefriendly.com/packages.html#local-build) | `makepkg -si` |")
    return "\n".join(rows)


def replace_block(text, marker, content):
    start, end = f"<!-- {marker}:start -->", f"<!-- {marker}:end -->"
    pattern = re.compile(re.escape(start) + r"[\s\S]*?" + re.escape(end))
    if len(pattern.findall(text)) != 1:
        raise ValueError(f"Expected exactly one {marker} block")
    return pattern.sub(lambda _: f"{start}\n{content}\n{end}", text)


def sync_package_review(records):
    path = ROOT / "PACKAGE-REVIEW.local.md"
    if not path.exists():
        return
    rows = ["| Package | Published version | Published date (UTC) | AUR maintainer |",
            "| --- | --- | --- | --- |"]
    for name, record in sorted(records.items()):
        published = record["binary_repo"] and "published_version" in record
        date = record.get("published_at") if published else None
        rows.append(
            f"| {name} | {record['published_version'] if published else 'Not published in this repository'} "
            f"| {date.astimezone(timezone.utc).date().isoformat() if date else 'Not recorded'} "
            f"| {'Yes' if record['aur_maintainer'] else 'No'} |"
        )
    path.write_text(replace_block(path.read_text(), "package-publications", "\n".join(rows)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--check", action="store_true", help="Check generated pages and README without changing files")
    action.add_argument("--allow-aur", metavar="PKGBASE", help="Exit successfully only for an approved AUR maintainer target")
    action.add_argument("--allow-binary", metavar="PKGBASE", help="Exit successfully only for an approved binary target")
    action.add_argument("--sync-package-review", action="store_true", help="Refresh publication state in the optional local package review")
    action.add_argument("--record-release", nargs=2, metavar=("PKGBASE", "VERSION"), help="Record a verified binary publication; does not publish or render")
    parser.add_argument("--published-at", type=datetime.fromisoformat, help="Publication timestamp with timezone; defaults to now in UTC")
    args = parser.parse_args()
    if args.published_at and not args.record_release:
        parser.error("--published-at requires --record-release")
    records = manifest()
    if args.sync_package_review:
        sync_package_review(records)
        return 0
    if args.record_release:
        name, version = args.record_release
        record = records.get(name, {})
        if not record.get("binary_repo") or not re.fullmatch(r"[A-Za-z0-9._+~-]+", version):
            raise ValueError("Release requires an approved binary package and a valid version")
        timestamp = args.published_at or datetime.now(timezone.utc).replace(microsecond=0)
        if timestamp.tzinfo is None or timestamp > datetime.now(timezone.utc):
            raise ValueError("Publication timestamp must have a timezone and cannot be in the future")
        if record.get("published_version") == version and "published_at" in record:
            sync_package_review(records)
            return 0
        path = ARCH / "manifest.toml"
        text = path.read_text()
        pattern = re.compile(r"(?ms)^\[" + re.escape(name) + r"\]\n.*?(?=^\[|\Z)")
        def update(match):
            block = re.sub(r'^published_at\s*=.*\n', '', match[0], flags=re.M)
            publication = f'published_version = "{version}"\npublished_at = {timestamp.isoformat()}'
            if "published_version" not in record:
                return block.replace(f"[{name}]\n", f"[{name}]\n{publication}\n", 1)
            return re.sub(r'^published_version\s*=.*$', publication, block, flags=re.M)
        path.write_text(pattern.sub(update, text))
        sync_package_review(manifest())
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
