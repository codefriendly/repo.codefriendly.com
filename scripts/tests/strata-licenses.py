#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 CodeFriendly
# SPDX-License-Identifier: MIT
"""Check the public license report and its fail-closed fallback policy."""
import json
from pathlib import Path
import subprocess
import tempfile

renderer = Path(__file__).resolve().parents[2] / "packages/arch/strata-fm/rust-licenses.py"
with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    (root / "siphasher-COPYING").write_text("Copyright 2016-2026 Frank Denis.\n")
    report = {"licenses": [
        {"name": "MIT License", "id": "MIT", "source_path": "LICENSE",
         "text": "Copyright (c) 2024 Original Author\nPermission notice.",
         "used_by": [{"crate": {"name": "example", "version": "2.0.0"}}]},
        {"name": "MIT License", "id": "MIT", "source_path": None,
         "text": "MIT License\n\nCopyright (c) <year> <copyright holders>\n\nPermission grant.",
         "used_by": [{"crate": {"name": "siphasher", "version": "1.0.3"}}]},
    ]}

    def render():
        (root / "input.json").write_text(json.dumps(report))
        (root / "output.md").unlink(missing_ok=True)
        return subprocess.run(["python3", str(renderer), str(root / "input.json"),
                               str(root), str(root / "output.md")],
                              capture_output=True, text=True)

    result = render()
    assert result.returncode == 0, result.stderr
    output = (root / "output.md").read_text()
    assert "example 2.0.0" in output and "siphasher 1.0.3" in output
    assert "Copyright (c) 2024 Original Author\nPermission notice." in output
    assert "Copyright 2016-2026 Frank Denis." in output
    assert "Permission grant." in output and "<copyright holders>" not in output

    # Both an unknown crate and a changed exception version must stop the build.
    for name, version in [("new-dependency", "1.0.3"), ("siphasher", "1.0.4")]:
        report["licenses"][1]["used_by"][0]["crate"] = {"name": name, "version": version}
        result = render()
        assert result.returncode != 0 and "Unreviewed license fallback" in result.stderr
        assert not (root / "output.md").exists()

print("Strata license report checks passed.")
