from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import seal_artifact


class SealArtifactTests(unittest.TestCase):
    def test_provenance_is_covered_by_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact = root / "artifact"
            artifact.mkdir()
            (artifact / "payload.txt").write_text("synthetic\n", encoding="utf-8")

            lock = root / "components.lock.json"
            lock.write_text(
                json.dumps({
                    "schema_version": 1,
                    "components": {
                        f"crisisweave-component-{index:02d}": "a" * 40
                        for index in range(11)
                    },
                }),
                encoding="utf-8",
            )

            seal_artifact.write_manifest(artifact, lock)
            seal_artifact.verify(artifact)

            manifest = (artifact / seal_artifact.MANIFEST).read_text(encoding="utf-8")
            self.assertIn(seal_artifact.PROVENANCE, manifest)

            provenance_path = artifact / seal_artifact.PROVENANCE
            provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
            provenance["umbrella_repository"] = "tampered/example"
            provenance_path.write_text(json.dumps(provenance), encoding="utf-8")

            with self.assertRaises(SystemExit):
                seal_artifact.verify(artifact)

    def test_symlink_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "payload.txt"
            target.write_text("synthetic\n", encoding="utf-8")
            link = root / "payload-link.txt"
            try:
                link.symlink_to(target.name)
            except (OSError, NotImplementedError):
                self.skipTest("symlinks are not available on this platform")

            with self.assertRaises(SystemExit):
                list(seal_artifact.files(root))


if __name__ == "__main__":
    unittest.main()
