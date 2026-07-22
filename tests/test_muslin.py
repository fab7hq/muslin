from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "scripts/build.py"


class MuslinTest(unittest.TestCase):
    def test_build_is_deterministic_and_muslin_calls_fab7(self) -> None:
        with tempfile.TemporaryDirectory(prefix="muslin-test-") as directory:
            temporary = Path(directory)
            first = temporary / "first"
            second = temporary / "second"
            for target in (first, second):
                subprocess.run(
                    [sys.executable, str(BUILDER), "--output", str(target)],
                    cwd=ROOT,
                    check=True,
                )
            self.assertEqual(_snapshot(first), _snapshot(second))

            fake_bin = temporary / "fake-bin"
            fake_bin.mkdir()
            fake_fab7 = fake_bin / "fab7"
            fake_fab7.write_text("#!/bin/sh\nprintf '0.2.0\\n'\n")
            fake_fab7.chmod(0o755)
            result = subprocess.run(
                [str(first / "bin/muslin"), "start", "--json"],
                env={**os.environ, "PATH": f"{fake_bin}:{os.environ['PATH']}"},
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["fab7_version"], "0.2.0")

    def test_archive_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory(prefix="muslin-archive-") as directory:
            temporary = Path(directory)
            outputs = [temporary / "first.zip", temporary / "second.zip"]
            for output in outputs:
                subprocess.run(
                    [sys.executable, str(BUILDER), "--archive", str(output)],
                    cwd=ROOT,
                    check=True,
                )
            self.assertEqual(
                hashlib.sha256(outputs[0].read_bytes()).hexdigest(),
                hashlib.sha256(outputs[1].read_bytes()).hexdigest(),
            )


def _snapshot(root: Path) -> list[tuple[str, int, str]]:
    rows = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        mode = path.stat().st_mode & 0o777
        value = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else "directory"
        rows.append((relative, mode, value))
    return rows


if __name__ == "__main__":
    unittest.main()
