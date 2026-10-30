#!/usr/bin/env python3
"""Check locked npm licenses and preserve notices from installed packages."""

import json
from pathlib import Path
import shutil
import sys

frontend = Path(sys.argv[1])
output = Path(sys.argv[2])
allowed = {
    "MIT", "ISC", "Apache-2.0", "BSD-2-Clause", "0BSD",
    "(MPL-2.0 OR Apache-2.0)",
}
radix_notices = {
    ("@radix-ui/number", "1.1.1"),
    ("@radix-ui/react-compose-refs", "1.1.2"),
    ("@radix-ui/react-context", "1.1.2"),
    ("@radix-ui/react-direction", "1.1.1"),
    ("@radix-ui/react-id", "1.1.1"),
    ("@radix-ui/react-use-callback-ref", "1.1.1"),
    ("@radix-ui/react-use-escape-keydown", "1.1.1"),
    ("@radix-ui/react-use-layout-effect", "1.1.1"),
    ("@radix-ui/react-use-previous", "1.1.1"),
    ("@radix-ui/react-use-rect", "1.1.1"),
    ("@radix-ui/react-use-size", "1.1.1"),
    ("@radix-ui/rect", "1.1.1"),
}
lock = json.loads((frontend / "package-lock.json").read_text())
rows = ["# Frontend dependency notices", "", "Runtime dependencies from the npm lockfile.", ""]
for relative, record in sorted(lock["packages"].items()):
    if not relative or record.get("dev"):
        continue
    package = frontend / relative
    if not package.exists():
        if record.get("optional"):
            continue
        raise SystemExit(f"Missing locked npm package: {relative}")
    metadata = json.loads((package / "package.json").read_text())
    license_name = record.get("license")
    if license_name not in allowed or metadata.get("version") != record["version"]:
        raise SystemExit(f"Review npm dependency: {relative}: {license_name}")
    name = metadata["name"]
    destination = output / "npm" / relative.removeprefix("node_modules/")
    notices = []
    # Preserve nested notices, but not those of another node_modules package.
    for path in sorted(package.rglob("*")):
        local = path.relative_to(package)
        if "node_modules" in local.parts or not path.is_file():
            continue
        if path.name.upper().startswith(("LICENSE", "LICENCE", "COPYING", "NOTICE", "COPYRIGHT", "PATENTS")):
            target = destination / local
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)
            notices.append(str(local))
    if not notices:
        # These MIT packages omit their notice from the npm tarball. Preserve
        # the original notice from the checksummed upstream repository source.
        if (name, record["version"]) in radix_notices and license_name == "MIT":
            supplement = "radix-LICENSE"
        elif (name, record["version"]) == ("react-remove-scroll-bar", "2.3.8") and license_name == "MIT":
            supplement = "react-remove-scroll-bar-LICENSE"
        else:
            raise SystemExit(f"No license notice found for {name}")
        destination.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(Path(__file__).parent / supplement, destination / "LICENSE")
        notices.append("LICENSE (upstream repository)")
    rows.extend([f"## {name} {record['version']}", "", f"License: {license_name}",
                 "", "Files: " + ", ".join(notices), ""])
output.mkdir(parents=True, exist_ok=True)
(output / "FRONTEND-LICENSES.md").write_text("\n".join(rows))
