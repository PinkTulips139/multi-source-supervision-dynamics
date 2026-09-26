"""Negative checks protect the hash/link gate without touching canonical artifacts."""
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('verify_package', ROOT / 'scripts/verify_package.py')
verifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)


class PackageGateTests(unittest.TestCase):
    def test_tampered_artifact_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            manifest_dir = root / verifier.STUDY / 'manifests'
            manifest_dir.mkdir(parents=True)
            digest = hashlib.sha256(b'known').hexdigest()
            (root / 'evidence.csv').write_bytes(b'wrong')
            item = dict(destination='evidence.csv', packaged_bytes=5, packaged_sha256=digest,
                        source_sha256=digest, transformation='byte-identical')
            (manifest_dir / 'evidence_manifest.json').write_text(json.dumps({'files': [item]}))
            with self.assertRaisesRegex(ValueError, 'Hash mismatch'):
                verifier.check_hashes(root)

    def test_broken_link_and_anchor_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'README.md').write_text('[missing](absent.md)')
            with self.assertRaisesRegex(ValueError, 'Broken link'):
                verifier.check_links(root)
            (root / 'README.md').write_text('[missing](target.md#absent)')
            (root / 'target.md').write_text('# Present\n')
            with self.assertRaisesRegex(ValueError, 'Broken anchor'):
                verifier.check_links(root)

    def test_actual_frozen_seed_and_result_bindings(self):
        self.assertEqual(verifier.check_results(ROOT)['fresh_path_cells'], 16)


if __name__ == '__main__':
    unittest.main()
