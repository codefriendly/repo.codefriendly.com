#!/usr/bin/env python3
"""Check npm notice preservation and fail-closed upstream fallbacks."""
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

helper = Path(__file__).resolve().parents[2] / "packages/arch/remanager/frontend-licenses.py"
with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    shutil.copyfile(helper, root / helper.name)
    (root / "radix-LICENSE").write_text("Original Radix copyright notice.\n")
    frontend = root / "frontend"
    package = frontend / "node_modules/@radix-ui/number"
    package.mkdir(parents=True)
    metadata = {"name": "@radix-ui/number", "version": "1.1.1"}
    record = {"version": "1.1.1", "license": "MIT"}

    def render():
        (package / "package.json").write_text(json.dumps(metadata))
        (frontend / "package-lock.json").write_text(json.dumps({
            "packages": {"node_modules/@radix-ui/number": record}}))
        shutil.rmtree(root / "output", ignore_errors=True)
        return subprocess.run(["python3", str(root / helper.name), str(frontend),
                               str(root / "output")], capture_output=True, text=True)

    result = render()
    assert result.returncode == 0, result.stderr
    notice = root / "output/npm/@radix-ui/number/LICENSE"
    assert notice.read_text() == "Original Radix copyright notice.\n"
    assert "@radix-ui/number 1.1.1" in (root / "output/FRONTEND-LICENSES.md").read_text()

    # New versions and unknown packages must not inherit a reviewed fallback.
    for name, version in [("@radix-ui/number", "1.1.2"), ("@radix-ui/unknown", "1.1.1")]:
        metadata.update(name=name, version=version)
        record["version"] = version
        result = render()
        assert result.returncode != 0 and "No license notice" in result.stderr

    metadata.update(name="example", version="1.1.1")
    (package / "LICENSE").write_text("Original example notice.\n")
    result = render()
    assert result.returncode == 0, result.stderr
    assert notice.read_text() == "Original example notice.\n"
    for license_name, version in [("Unreviewed", "1.1.1"), ("MIT", "1.1.2")]:
        record.update(license=license_name, version=version)
        result = render()
        assert result.returncode != 0 and "Review npm dependency" in result.stderr

print("reManager license report checks passed.")
