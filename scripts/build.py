#!/usr/bin/env python3
"""Build one deterministic Muslin extension package or ZIP artifact."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import stat
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
IDENTITY = {
    "name": "muslin",
    "publisher": "fab7hq",
    "repository": "https://github.com/fab7hq/muslin",
    "version": "0.1.0",
    "fab7_min": "0.2.0",
    "fab7_max_exclusive": "0.3.0",
    "executable": "muslin",
    "capabilities": ["smoke-test"],
    "hosts": ["claude", "codex"],
}
FIXED_TIME = (1980, 1, 1, 0, 0, 0)


def build(output: Path) -> None:
    if output.exists():
        raise SystemExit(f"output already exists: {output}")
    output.mkdir(parents=True)
    executable = output / "bin/muslin"
    executable.parent.mkdir(parents=True)
    shutil.copyfile(ROOT / "src/muslin.py", executable)
    executable.chmod(0o755)
    shutil.copyfile(ROOT / "LICENSE", output / "LICENSE")
    (output / "LICENSE").chmod(0o644)

    for host in ("claude", "codex"):
        shutil.copytree(
            ROOT / "plugins" / host / "muslin",
            output / "hosts" / host / "plugins" / "muslin",
        )
        for path in (output / "hosts" / host / "plugins" / "muslin").rglob("*"):
            if path.is_file():
                path.chmod(0o644)

    _write_json(
        output / "hosts/claude/.claude-plugin/marketplace.json",
        {
            "name": "muslin",
            "description": "Muslin test extension for Fab7.",
            "owner": {"name": "Fab7", "url": "https://github.com/fab7hq"},
            "plugins": [
                {
                    "name": "muslin",
                    "source": "./plugins/muslin",
                    "description": "Minimal Fab7 extension-distribution fixture.",
                    "version": "0.1.0",
                }
            ],
        },
    )
    _write_json(
        output / "hosts/codex/.agents/plugins/marketplace.json",
        {
            "name": "muslin",
            "interface": {"displayName": "Muslin"},
            "plugins": [
                {
                    "name": "muslin",
                    "source": {"source": "local", "path": "./plugins/muslin"},
                    "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
                    "category": "Productivity",
                }
            ],
        },
    )

    rows = []
    for path in sorted(candidate for candidate in output.rglob("*") if candidate.is_file()):
        rows.append(
            {
                "path": path.relative_to(output).as_posix(),
                "mode": "0755" if path == executable else "0644",
                "sha256": "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        )
    _write_json(output / "extension.json", {"schema": 1, **IDENTITY, "files": rows})


def archive(package: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise SystemExit(f"archive already exists: {destination}")
    with destination.open("w+b") as raw:
        with zipfile.ZipFile(raw, "w", compression=zipfile.ZIP_STORED) as output:
            for path in sorted(candidate for candidate in package.rglob("*") if candidate.is_file()):
                relative = path.relative_to(package).as_posix()
                mode = stat.S_IFREG | (0o755 if relative == "bin/muslin" else 0o644)
                info = zipfile.ZipInfo(relative, FIXED_TIME)
                info.create_system = 3
                info.external_attr = mode << 16
                info.compress_type = zipfile.ZIP_STORED
                output.writestr(info, path.read_bytes())


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n")
    path.chmod(0o644)


def main() -> int:
    parser = argparse.ArgumentParser()
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--output", type=Path)
    target.add_argument("--archive", type=Path)
    args = parser.parse_args()
    if args.output is not None:
        build(args.output)
    else:
        with tempfile.TemporaryDirectory(prefix="muslin-build-") as directory:
            package = Path(directory) / "muslin"
            build(package)
            archive(package, args.archive)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
