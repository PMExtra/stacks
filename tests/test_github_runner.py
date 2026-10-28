"""Persistent runner contracts, rendered through upgrade without a Docker daemon."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class GitHubRunnerComposeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="stacks-github-config-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        shutil.copyfile(ROOT / "upgrade", self.root / "upgrade")
        self.stack = self.root / "github"
        (self.stack / "optional").mkdir(parents=True)
        for name in ("compose.yaml", ".env.example", "optional/compose.runner.yaml"):
            shutil.copyfile(ROOT / "github" / name, self.stack / name)
        self.env = {key: os.environ[key] for key in ("PATH", "HOME", "DOCKER_CONFIG")
                    if key in os.environ}

    def render(self, settings=None, enabled=True):
        link = self.stack / "compose.runner.yaml"
        if enabled and not link.is_symlink():
            link.symlink_to("optional/compose.runner.yaml")
        (self.stack / ".env").write_text("\n".join(
            f"{key}={value}" for key, value in (settings or {}).items()) + "\n")
        return subprocess.run(
            ["bash", "./upgrade", "-n", "github", "config", "--format", "json"],
            cwd=self.root, env=self.env, text=True, capture_output=True)

    def config(self, settings):
        result = self.render(settings)
        self.assertEqual(result.returncode, 0, result.stderr)
        # upgrade prints a status line before Compose's JSON.
        return json.loads(result.stdout[result.stdout.index("{"):])

    def test_base_does_not_enable_optional_runner(self):
        result = self.render(enabled=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        config = json.loads(result.stdout[result.stdout.index("{"):])
        self.assertEqual(config["services"], {})

    def test_name_required_even_with_reused_identity(self):
        for name in (None, ""):
            settings = {} if name is None else {"RUNNER_NAME": name}
            result = self.render(settings)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Set a unique RUNNER_NAME", result.stderr)

    def test_repo_org_and_bootstrap_or_reused_identity(self):
        for scope, target in (("repo", {"REPO_URL": "https://github.com/example/project"}),
                              ("org", {"ORG_NAME": "example"})):
            for token in (None, "", "dummy-registration-token"):
                with self.subTest(scope=scope, token=token):
                    settings = dict(RUNNER_NAME="unique-dev-runner", RUNNER_SCOPE=scope,
                                    TAG="ubuntu-noble", http_proxy="http://proxy.example.test:3128",
                                    https_proxy="http://proxy.example.test:3128",
                                    no_proxy="localhost,db.example.test", **target)
                    if token is not None:
                        settings["RUNNER_TOKEN"] = token
                    config = self.config(settings)
                    self.assertEqual(set(config["services"]), {"runner"})
                    runner = config["services"]["runner"]
                    self.assertEqual(runner["container_name"], "github_runner")
                    self.assertEqual(runner["image"], "myoung34/github-runner:ubuntu-noble")
                    environment = runner["environment"]
                    for key, value in settings.items():
                        self.assertEqual(environment[key], value)
                    if token is None:
                        self.assertNotIn("RUNNER_TOKEN", environment)
                    self.assertEqual(environment["DISABLE_AUTOMATIC_DEREGISTRATION"], "true")
                    self.assertEqual(environment["RUN_AS_ROOT"], "false")
                    self.assertEqual(environment["UNSET_CONFIG_VARS"], "true")
                    for flag in ("EPHEMERAL", "DISABLE_AUTO_UPDATE", "START_DOCKER_SERVICE"):
                        self.assertNotIn(flag, environment)
                    self.assertEqual(config["networks"]["default"]["name"], "github")
                    self.assertEqual(runner["networks"], {"default": None})
                    mounts = {m["source"]: m["target"] for m in runner["volumes"]}
                    self.assertEqual(mounts, {"runner_config": environment["CONFIGURED_ACTIONS_RUNNER_FILES_DIR"],
                                              "runner_work": environment["RUNNER_WORKDIR"]})
                    self.assertTrue(all(m["type"] == "volume" for m in runner["volumes"]))
                    for volume in mounts:
                        self.assertEqual(config["volumes"][volume]["name"], f"github_{volume}")
                    for key in ("ports", "privileged", "devices", "healthcheck", "platform",
                                "build", "user", "network_mode"):
                        self.assertNotIn(key, runner)
                    self.assertIsNone(runner.get("entrypoint"))
                    self.assertIsNone(runner.get("command"))

    def test_example_and_default_tag(self):
        settings = dict(line.split("=", 1) for line in
                        (self.stack / ".env.example").read_text().splitlines()
                        if line and not line.startswith("#"))
        settings.update(RUNNER_NAME="unique-dev-runner", REPO_URL="https://github.com/example/project")
        for tag in (None, ""):
            if tag is None:
                settings.pop("TAG", None)
            else:
                settings["TAG"] = tag
            config = self.config(settings)
            self.assertEqual(config["services"]["runner"]["image"], "myoung34/github-runner:latest")
