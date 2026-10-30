#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Render cargo-about JSON. Reject unreviewed generic license fallbacks."""
import json
from pathlib import Path
import sys

report = json.loads(Path(sys.argv[1]).read_text())
sources = Path(sys.argv[2])
output = ["# Rust dependency licenses\n",
          "Generated from the locked native dependency graph. Bundled assets and "
          "UnRAR have separate notices in THIRD_PARTY_LICENSES.md and data/licenses/.\n"]

# These published crates omit license files. Review a new version before using
# these exceptions. Do not replace missing copyright notices with invented ones.
reviewed = {("rquickjs-core", "0.13.0"), ("siphasher", "1.0.3"),
            ("poppler-rs", "0.26.0"), ("poppler-sys-rs", "0.26.0")}
for license in report["licenses"]:
    crates = [entry["crate"] for entry in license["used_by"]]
    output.append(f"## {license['name']}\n")
    for crate in crates:
        output.append(f"- {crate['name']} {crate['version']}\n")
    if license["source_path"] is not None:
        output.append(f"\n```text\n{license['text']}\n```\n")
        continue
    for crate in crates:
        identity = (crate["name"], crate["version"])
        if license["id"] != "MIT" or identity not in reviewed:
            sys.exit(f"Unreviewed license fallback: {identity}. Add verified notices before building.")
        output.append(f"\n### {crate['name']} {crate['version']}\n")
        if crate["name"] == "rquickjs-core":
            output.append(f"\n```text\n{(sources / 'rquickjs-LICENSE').read_text()}\n```\n")
            continue
        if crate["name"] == "siphasher":
            output.append(f"\n```text\n{(sources / 'siphasher-COPYING').read_text()}\n```\n")
        else:
            output.append("\nUpstream declares MIT in Cargo.toml but supplies no separate license "
                          "or copyright file. The published metadata follows. "
                          "The standard MIT grant is reproduced below it.\n")
            manifest = Path(crate["manifest_path"]).read_text()
            output.append(f"\n```toml\n{manifest}\n```\n")
        text = license["text"].replace("Copyright (c) <year> <copyright holders>\n\n", "")
        output.append(f"\n```text\n{text}\n```\n")

Path(sys.argv[3]).write_text("\n".join(output))
