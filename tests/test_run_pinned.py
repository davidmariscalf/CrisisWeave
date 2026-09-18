from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

import run_pinned


class RunPinnedTests(unittest.TestCase):
    def test_clean_component_worktree_removes_untracked_and_ignored_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "component"
            repo.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.email", "ci@example.invalid"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.name", "CI"], cwd=repo, check=True)

            (repo / ".gitignore").write_text("cache/\n", encoding="utf-8")
            (repo / "tracked.txt").write_text("locked\n", encoding="utf-8")
            subprocess.run(["git", "add", ".gitignore", "tracked.txt"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-q", "-m", "fixture"], cwd=repo, check=True)

            (repo / "untracked.txt").write_text("stale\n", encoding="utf-8")
            cache = repo / "cache"
            cache.mkdir()
            (cache / "ignored.bin").write_bytes(b"stale")

            run_pinned.clean_component_worktree(repo)

            self.assertFalse((repo / "untracked.txt").exists())
            self.assertFalse(cache.exists())
            status = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=repo,
                check=True,
                text=True,
                stdout=subprocess.PIPE,
            ).stdout
            self.assertEqual(status, "")


if __name__ == "__main__":
    unittest.main()
