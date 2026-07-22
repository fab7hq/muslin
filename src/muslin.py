#!/usr/bin/env python3
"""Minimal Fab7 extension fixture."""

from __future__ import annotations

import argparse
import json
import subprocess


def main() -> int:
    parser = argparse.ArgumentParser(prog="muslin")
    commands = parser.add_subparsers(dest="command", required=True)
    start = commands.add_parser("start", help="observe the installed Fab7 binary")
    start.add_argument("--json", action="store_true")
    args = parser.parse_args()

    try:
        process = subprocess.run(
            ["fab7", "--version"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        data = {"ok": False, "extension": "muslin", "error": str(exc)}
        if args.json:
            print(json.dumps(data, sort_keys=True))
        else:
            print(f"Muslin could not invoke Fab7: {exc}")
        return 1

    data = {
        "ok": process.returncode == 0,
        "extension": "muslin",
        "fab7_version": process.stdout.strip(),
    }
    if args.json:
        print(json.dumps(data, sort_keys=True))
    else:
        print(f"Muslin started with Fab7 {data['fab7_version']}")
    return 0 if data["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
