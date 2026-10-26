"""Run only the read-only guard library with local fixtures and mocked TV tools.

Never source autoroot.sh or invoke its absolute-path installation code.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


GUARDS = Path(__file__).resolve().parents[1] / "wwwroot" / "preinstall-guards.sh"


@unittest.skipUnless(shutil.which("node"), "node is required to test the TV JSON parser")
class PreinstallGuardTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.marker = self.root / "devmode_enabled"
        self.package = self.root / "hbchannel.ipk"
        self.package.write_bytes(b"local test fixture, never installed")
        self.digest = hashlib.sha256(self.package.read_bytes()).hexdigest()
        self.apps = {"returnValue": True, "apps": [{"id": "com.webos.app.home"}]}
        self.previous_state = [self.root / name for name in ("start-devmode.sh", "start-devmode.sh.backup", "webosbrew")]
        self.bin = self.root / "bin"
        self.bin.mkdir()
        luna = self.bin / "luna-send"
        luna.write_text('#!/bin/sh\nprintf "%s\\n" "$TEST_RESPONSE"\nexit "$TEST_LUNA_EXIT"\n')
        luna.chmod(0o755)

    def check(self, *, uid="0", response=None, luna_exit="0", hash_exit="0", digest=None):
        env = dict(os.environ, TEST_UID=uid, TEST_LUNA_EXIT=luna_exit,
                   TEST_HASH_EXIT=hash_exit, TEST_DIGEST=digest or self.digest,
                   TEST_RESPONSE=json.dumps(self.apps) if response is None else response)
        # id/luna-send are local stubs. Hash stub computes a real fixture SHA256
        # through Python, so altered bytes are tested rather than trusted output.
        env["TEST_PYTHON"] = sys.executable
        env["PATH"] = str(self.bin) + os.pathsep + env["PATH"]
        return subprocess.run([
            "/bin/sh", "-c", '''
                . "$1"
                id() { printf '%s\n' "$TEST_UID"; }
                sha256sum() {
                    [ "$TEST_HASH_EXIT" = 0 ] || return "$TEST_HASH_EXIT"
                    "$TEST_PYTHON" -c 'import hashlib,sys; print(hashlib.sha256(open(sys.argv[1], "rb").read()).hexdigest()+"  "+sys.argv[1])' "$2"
                }
                preinstall_checks "$2" "$3" "$TEST_DIGEST" "$4" "$5" "$6" || exit 1
                printf 'READY\n'
            ''', "guard-test", str(GUARDS), str(self.marker), str(self.package),
            *map(str, self.previous_state),
        ], env=env, text=True, capture_output=True, timeout=10)

    def assertRefused(self, result, message):
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("READY", result.stdout)
        self.assertIn(message, result.stderr)

    def test_valid_preflight_does_not_mutate_fixture(self):
        before = self.package.read_bytes()
        result = self.check()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "READY\n")
        self.assertFalse(self.marker.exists())
        self.assertEqual(self.package.read_bytes(), before)

    def test_refuses_non_root(self):
        self.assertRefused(self.check(uid="1000"), "root privileges")

    def test_refuses_existing_marker_without_changing_it(self):
        self.marker.write_text("existing marker")
        self.assertRefused(self.check(), "path already exists")
        self.assertEqual(self.marker.read_text(), "existing marker")

    def test_refuses_existing_directory_and_dangling_symlink(self):
        self.marker.mkdir()
        self.assertRefused(self.check(), "path already exists")
        self.marker.rmdir()
        self.marker.symlink_to(self.root / "absent")
        self.assertRefused(self.check(), "path already exists")
        self.assertTrue(self.marker.is_symlink())

    def test_refuses_installed_developer_mode(self):
        self.apps["apps"].append({"id": "com.palmdts.devmode"})
        self.assertRefused(self.check(), "Developer Mode app is installed")

    def test_refuses_existing_homebrew_channel(self):
        self.apps["apps"].append({"id": "org.webosbrew.hbchannel"})
        self.assertRefused(self.check(), "Homebrew Channel already exists")

    def test_refuses_abandoned_root_state_without_changing_it(self):
        for path in self.previous_state:
            with self.subTest(path=path):
                path.write_text("preserve me")
                self.assertRefused(self.check(), "path already exists")
                self.assertEqual(path.read_text(), "preserve me")
                path.unlink()
                path.symlink_to(self.root / "missing")
                self.assertRefused(self.check(), "path already exists")
                self.assertTrue(path.is_symlink())
                path.unlink()

    def test_installer_offers_no_reboot_or_success_claim(self):
        installer = (GUARDS.parent / "autoroot.sh").read_text()
        self.assertNotIn("machineReboot", installer)
        self.assertNotIn("Rooting complete", installer)
        self.assertIn("root access and persistence are not yet verified", installer)

    def test_guard_is_required_and_available_to_payload_loader(self):
        import slopbro
        self.assertIn("preinstall-guards.sh", slopbro.SERVICE_FILES)
        files = slopbro.required_files()
        self.assertIn("preinstall-guards.sh", files)
        root, _, _, _ = slopbro.resolve_asset_root("dir", files)
        self.assertEqual(slopbro._read_filesystem_file(root, "preinstall-guards.sh"), GUARDS.read_bytes())

    @unittest.skipIf(sys.version_info < (3, 12), "packager requires Python 3.12+")
    def test_single_file_artifact_contains_usable_guard(self):
        import importlib.util
        repo = GUARDS.parents[1]
        output = self.root / "packed.py"
        subprocess.run([
            sys.executable, str(repo / "tools/package_single_file.py"),
            "--source", str(repo / "slopbro.py"),
            "--wwwroot", str(GUARDS.parent), "--out", str(output),
        ], check=True, capture_output=True, text=True, timeout=10)
        spec = importlib.util.spec_from_file_location("slopbro_test_artifact", output)
        packed = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(packed)
        packed.resolve_asset_root("embedded", packed.required_files())
        self.assertEqual(packed._read_embedded_file("preinstall-guards.sh"), GUARDS.read_bytes())

    def test_refuses_failed_or_unknown_app_query(self):
        self.assertRefused(self.check(luna_exit="1"), "cannot query")
        for value in ("garbage", "null", "[]", '{}',
                      '{"returnValue":false,"apps":[]}',
                      '{"returnValue":true}',
                      '{"returnValue":true,"apps":[]}',
                      '{"returnValue":true,"apps":[{}]}'):
            with self.subTest(value=value):
                self.assertRefused(self.check(response=value), "Refusing installation")

    def test_refuses_modified_package(self):
        self.package.write_bytes(b"changed")
        self.assertRefused(self.check(), "SHA256 does not match")

    def test_refuses_missing_or_symlink_package(self):
        self.package.unlink()
        self.assertRefused(self.check(), "package is missing")
        self.package.symlink_to(self.root / "absent")
        self.assertRefused(self.check(), "package is missing")

    def test_refuses_failed_hash_tool(self):
        self.assertRefused(self.check(hash_exit="127"), "cannot verify package")


if __name__ == "__main__":
    unittest.main()
