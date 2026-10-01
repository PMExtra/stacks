"""Data-layout checks using temporary files, a Docker stub and Compose parsing."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

import test_upgrade


ROOT = Path(__file__).resolve().parents[1]
LAYOUTS = ("compose.data.yaml", "compose.data_legacy.yaml")


def parse_compose(stack, overlays, tag="18"):
    with tempfile.TemporaryDirectory(prefix="stacks-data-config-") as temporary:
        directory = Path(temporary)
        shutil.copyfile(ROOT / stack / "compose.yaml", directory / "compose.yaml")
        (directory / ".env").write_text("")
        command = ["docker", "compose", "-p", stack, "-f", str(directory / "compose.yaml")]
        for name in overlays:
            shutil.copyfile(ROOT / stack / "optional" / name, directory / name)
            command += ["-f", str(directory / name)]
        env = dict(os.environ, POSTGRES_PASSWORD="test-only")
        env.pop("TAG", None)
        if stack == "postgres" and tag is not None:
            env["TAG"] = tag
        result = subprocess.run(command + ["config", "--format", "json"],
                                env=env,
                                text=True, capture_output=True)
        if result.returncode:
            raise AssertionError(result.stderr)
        return json.loads(result.stdout)


class DataLayoutHookTests(unittest.TestCase):
    def setUp(self):
        self.cli = test_upgrade.UpgradeTests()
        self.cli.setUp()
        self.addCleanup(self.cli.doCleanups)
        shutil.copyfile(ROOT / "postgres" / "before-upgrade.sh", self.cli.stack / "before-upgrade.sh")

    def check_layouts(self, layouts, expected_success):
        for name in layouts:
            # The hook only checks file existence, not its contents.
            (self.cli.stack / name).write_text("services: {}\n")
        for args in ((str(self.cli.stack),), ("--no-up", str(self.cli.stack), "config"),
                     ("--no-up", str(self.cli.stack), "down")):
            with self.subTest(layouts=layouts, args=args):
                if self.cli.log.exists():
                    self.cli.log.unlink()
                result = self.cli.run_upgrade(*args)
                if expected_success:
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertTrue(self.cli.log.exists())
                else:
                    self.assertNotEqual(result.returncode, 0)
                    self.assertFalse(self.cli.log.exists())
                    self.assertIn("Choose a PostgreSQL data layout", result.stderr)
                    for name in LAYOUTS:
                        self.assertIn(f"ln -s optional/{name} ./", result.stderr)
                        self.assertFalse((self.cli.stack / name).exists())

    def test_no_layout_stops_all_operations(self):
        self.check_layouts((), False)

    def test_data_allows_all_operations(self):
        self.check_layouts((LAYOUTS[0],), True)

    def test_legacy_allows_all_operations(self):
        self.check_layouts((LAYOUTS[1],), True)

    def test_both_allow_all_operations(self):
        self.check_layouts(LAYOUTS, True)


class DataLayoutComposeTests(unittest.TestCase):
    def test_postgres_requires_explicit_nonempty_tag(self):
        for tag in (None, ""):
            for overlays in ((), ("compose.build.yaml",)):
                with self.subTest(tag=tag, overlays=overlays):
                    with self.assertRaisesRegex(AssertionError, "Set TAG explicitly"):
                        parse_compose("postgres", overlays, tag=tag)

    def test_postgres_preserves_explicit_tags(self):
        for tag in ("17", "18", "latest"):
            for overlays in ((), ("compose.build.yaml",)):
                with self.subTest(tag=tag, overlays=overlays):
                    config = parse_compose("postgres", overlays, tag=tag)
                    image = "localhost/build/postgres" if overlays else "postgres"
                    self.assertEqual(config["services"]["postgres"]["image"],
                                     f"{image}:{tag}")

    def test_postgres_volume_names_targets_and_pgdata(self):
        for layouts in ((), (LAYOUTS[0],), (LAYOUTS[1],), LAYOUTS):
            with self.subTest(layouts=layouts):
                config = parse_compose("postgres", layouts)
                service = config["services"]["postgres"]
                mounts = service.get("volumes", [])
                targets = {"/var/lib/postgresql" if name == LAYOUTS[0]
                           else "/var/lib/postgresql/data" for name in layouts}
                self.assertEqual({mount["target"] for mount in mounts}, targets)
                self.assertTrue(all(mount["source"] == "data" for mount in mounts))
                if layouts:
                    self.assertEqual(config["volumes"]["data"]["name"], "postgres_data")
                if LAYOUTS[1] in layouts:
                    self.assertEqual(service["environment"]["PGDATA"], "/var/lib/postgresql/data")
                else:
                    self.assertNotIn("PGDATA", service.get("environment", {}))

    def test_sub2api_postgres18_parent_mount(self):
        config = parse_compose("sub2api", ("compose.postgres.yaml",))
        service = config["services"]["postgres"]
        self.assertEqual(service["image"], "postgres:18-alpine")
        self.assertEqual(len(service["volumes"]), 1)
        self.assertEqual(service["volumes"][0]["source"], "postgres_data")
        self.assertEqual(service["volumes"][0]["target"], "/var/lib/postgresql")
        self.assertEqual(config["volumes"]["postgres_data"]["name"], "sub2api_postgres_data")
        self.assertNotIn("PGDATA", service["environment"])
        self.assertEqual(config["services"]["sub2api"]["volumes"][0]["target"], "/app/data")

    def test_sub2api_external_database_needs_no_layout_choice(self):
        config = parse_compose("sub2api", ())
        self.assertNotIn("postgres", config["services"])
        cli = test_upgrade.UpgradeTests()
        cli.setUp()
        self.addCleanup(cli.doCleanups)
        shutil.copytree(ROOT / "sub2api", cli.stack, dirs_exist_ok=True)
        (cli.stack / ".env").write_text("")
        result = cli.run_upgrade("--no-up", str(cli.stack), "config")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("Choose a PostgreSQL data layout", result.stderr)
        self.assertTrue(cli.log.exists())


if __name__ == "__main__":
    unittest.main()
