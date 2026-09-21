"""Real-mount regression test; opt in because it needs the host FUSE device."""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

pytestmark = pytest.mark.integration


@pytest.mark.skipif(os.environ.get("LMDB_FS_RUN_FUSE_TESTS") != "1", reason="set LMDB_FS_RUN_FUSE_TESTS=1")
def test_mounted_lmdb_fs_supports_normal_reads(tmp_path: Path) -> None:
    root = Path(__file__).parents[1]
    corpus = tmp_path / "corpus"
    mountpoint = tmp_path / "mount"
    subprocess.run(
        [sys.executable, root / "tools/generate_data.py", "--nodes", "100", "--seed", "42", "--output", corpus],
        check=True,
    )
    subprocess.run(
        [sys.executable, "-m", "lmdb_fs.cli", "build-index", "--metadata", corpus / "metadata.jsonl", "--db", corpus / "index.lmdb"],
        check=True,
    )
    mountpoint.mkdir()
    server = subprocess.Popen(
        [sys.executable, "-m", "lmdb_fs.cli", "mount", "--db", corpus / "index.lmdb", "--mountpoint", mountpoint]
    )
    try:
        for _ in range(50):
            if os.path.ismount(mountpoint):
                break
            time.sleep(0.1)
        assert os.path.ismount(mountpoint)
        year = sorted(entry.name for entry in mountpoint.glob("year=*") if entry.is_dir())[0]
        disease = sorted(entry.name for entry in (mountpoint / year).glob("disease=*") if entry.is_dir())[0]
        forward = sorted(entry.name for entry in (mountpoint / year / disease).iterdir() if entry.is_file())
        reverse = sorted(entry.name for entry in (mountpoint / disease / year).iterdir() if entry.is_file())
        assert forward and forward == reverse
        assert "lmdb-fs reusable synthetic payload" in (mountpoint / year / disease / forward[0]).read_text()
        with pytest.raises(PermissionError):
            (mountpoint / "cannot-write").touch()
    finally:
        if os.path.ismount(mountpoint):
            subprocess.run(["fusermount3", "-u", mountpoint], check=True)
        server.wait(timeout=10)
