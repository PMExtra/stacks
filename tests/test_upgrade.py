"""Isolated CLI regressions; Docker is stubbed and no services are started."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


UPGRADE = Path(os.environ.get("UPGRADE_UNDER_TEST", Path(__file__).resolve().parents[1] / "upgrade"))


class UpgradeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="stacks-upgrade-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.stack = self.root / "stack with spaces"
        self.stack.mkdir()
        (self.stack / "compose.yaml").write_text("services: {}\n")
        self.log = self.root / "docker.jsonl"
        docker = self.root / "docker"
        docker.write_text(f"#!{sys.executable}\n" + '''import json, os, sys
if sys.argv[1:] == ["compose", "version"]:
    print("Docker Compose version v2.40.3")
else:
    with open(os.environ["TEST_DOCKER_LOG"], "a") as log:
        log.write(json.dumps([os.getcwd(), sys.argv[1:]]) + "\\n")
''')
        docker.chmod(0o700)
        self.env = dict(os.environ, PATH=f"{self.root}:{os.environ['PATH']}", TEST_DOCKER_LOG=str(self.log))

    def run_upgrade(self, *args, cwd=None):
        return subprocess.run(["bash", str(UPGRADE), *args], cwd=cwd or self.stack,
                              env=self.env, text=True, capture_output=True)

    def calls(self):
        return [json.loads(line) for line in self.log.read_text().splitlines()]

    def test_explicit_stack_and_compose_arguments(self):
        result = self.run_upgrade("--no-up", str(self.stack), "config", "--quiet", cwd=self.root)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.calls(), [[str(self.stack), ["compose", "-f", "compose.yaml", "config", "--quiet"]]])

    def test_hook_argument_values_are_preserved(self):
        output = self.stack / "hook-args"
        (self.stack / "before-upgrade.sh").write_text('printf "%s\\n" "${hook_args[@]}" > hook-args\n')
        result = self.run_upgrade("--no-up", "--hook-args", "two words", "-a", "second", str(self.stack), "config")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(output.read_text(), "two words\nsecond\n")
        self.assertEqual(self.calls()[0][1], ["compose", "-f", "compose.yaml", "config"])

    def test_missing_hook_argument_is_rejected_before_docker_action(self):
        for option in ("--hook-args", "-a"):
            with self.subTest(option=option):
                result = self.run_upgrade(option)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(f"{option} requires an argument.", result.stderr)
                self.assertFalse(self.log.exists())


if __name__ == "__main__":
    unittest.main()
