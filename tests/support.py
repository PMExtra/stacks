"""Shared isolated upgrade fixture; Docker calls are recorded, never executed."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


UPGRADE = Path(os.environ.get("UPGRADE_UNDER_TEST", Path(__file__).resolve().parents[1] / "upgrade"))


class UpgradeTestCase(unittest.TestCase):
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
