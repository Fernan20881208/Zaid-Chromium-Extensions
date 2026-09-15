import hashlib
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from common import ROOT, revision
from package_apk import validate_apk
from source_contract import check_file
from preflight import inspect


class ApkValidationTest(unittest.TestCase):
    def make_apk(self, directory, libraries, manifest=True):
        path = Path(directory) / 'test.apk'
        with zipfile.ZipFile(path, 'w') as apk:
            if manifest:
                apk.writestr('AndroidManifest.xml', b'test manifest')
            for name, machine, elf_class in libraries:
                header = bytearray(64)
                header[:6] = b'\x7fELF' + bytes([elf_class, 1])
                struct.pack_into('<H', header, 18, machine)
                apk.writestr(name, header)
        return path

    def test_arm64_payload(self):
        with tempfile.TemporaryDirectory() as directory:
            apk = self.make_apk(directory, [('lib/arm64-v8a/libchrome.so', 183, 2)])
            self.assertEqual(validate_apk(apk), 1)

    def test_rejects_wrong_architecture_even_with_arm64_folder_name(self):
        with tempfile.TemporaryDirectory() as directory:
            apk = self.make_apk(directory, [('lib/arm64-v8a/libchrome.so', 62, 2)])
            with self.assertRaisesRegex(ValueError, 'AArch64'):
                validate_apk(apk)

    def test_rejects_mixed_abi(self):
        with tempfile.TemporaryDirectory() as directory:
            apk = self.make_apk(directory, [('lib/arm64-v8a/libchrome.so', 183, 2),
                                             ('lib/armeabi-v7a/libchrome.so', 40, 1)])
            with self.assertRaisesRegex(ValueError, 'only ARM64'):
                validate_apk(apk)

    def test_rejects_empty_or_non_apk_archive(self):
        with tempfile.TemporaryDirectory() as directory:
            for manifest in (True, False):
                with self.subTest(manifest=manifest):
                    with self.assertRaises(ValueError):
                        validate_apk(self.make_apk(directory, [], manifest=manifest))


class SourceContractTest(unittest.TestCase):
    def test_source_drift_is_rejected(self):
        content = b'ExtensionRegistry'
        contract = {'sha256': hashlib.sha256(content).hexdigest(), 'contains': ['ExtensionRegistry']}
        self.assertEqual(check_file('test.cc', content, contract), contract['sha256'])
        with self.assertRaisesRegex(ValueError, 'Pinned source differs'):
            check_file('test.cc', b'Changed source', contract)

    def test_missing_required_integration_is_rejected(self):
        content = b'ExtensionRegistry'
        contract = {'sha256': hashlib.sha256(content).hexdigest(), 'contains': ['ServiceWorkerManager']}
        with self.assertRaisesRegex(ValueError, 'Missing upstream integration'):
            check_file('test.cc', content, contract)

    def test_locked_revision_and_smoke_fixture(self):
        lock = revision()
        self.assertEqual(lock['channel'], 'stable')
        fixture = ROOT / 'tests/fixtures/mv3-smoke'
        manifest = json.loads((fixture / 'manifest.json').read_text())
        self.assertEqual(manifest['manifest_version'], 3)
        self.assertTrue((fixture / manifest['background']['service_worker']).is_file())
        self.assertEqual(manifest['host_permissions'], ['https://example.com/*'])

    @patch('preflight.shutil.disk_usage')
    def test_small_host_is_rejected_before_source_download(self, disk):
        disk.return_value.free = 30 * 1024**3
        result = inspect(ROOT)
        self.assertFalse(result['ready'])
        self.assertTrue(any('free' in problem for problem in result['problems']))


if __name__ == '__main__':
    unittest.main()
