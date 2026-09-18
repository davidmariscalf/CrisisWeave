from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

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


    def test_checkout_component_verifies_the_checked_out_sha(self) -> None:
        expected_sha = "a" * 40
        calls = []

        def fake_run(cmd, *, cwd=None):
            calls.append(tuple(cmd))
            if cmd == ["git", "status", "--porcelain"]:
                return ""
            if cmd == ["git", "rev-parse", "HEAD"]:
                return expected_sha
            return ""

        with tempfile.TemporaryDirectory() as tmp, patch.object(run_pinned, "run", side_effect=fake_run):
            run_pinned.checkout_component(Path(tmp), "owner", "crisisweave-test", expected_sha)

        self.assertIn(("git", "clean", "-ffdx"), calls)
        self.assertIn(("git", "rev-parse", "HEAD"), calls)


if __name__ == "__main__":
    unittest.main()
