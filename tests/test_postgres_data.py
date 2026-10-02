"""Data-layout checks using temporary files, a Docker stub and Compose parsing."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from support import UpgradeTestCase


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
        env = {key: os.environ[key] for key in ("PATH", "HOME", "DOCKER_CONFIG")
               if key in os.environ}
        env["POSTGRES_PASSWORD"] = "test-only"
        if stack == "postgres" and tag is not None:
            env["TAG"] = tag
        result = subprocess.run(command + ["config", "--format", "json"],
                                env=env,
                                text=True, capture_output=True, check=True)
        return json.loads(result.stdout)


class DataLayoutHookTests(UpgradeTestCase):
    def setUp(self):
        super().setUp()
        shutil.copyfile(ROOT / "postgres" / "before-upgrade.sh", self.stack / "before-upgrade.sh")

    def test_no_layout_stops_all_operations(self):
        for args in ((str(self.stack),), ("--no-up", str(self.stack), "config"),
                     ("--no-up", str(self.stack), "down")):
            with self.subTest(args=args):
                result = self.run_upgrade(*args)
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse(self.log.exists())
                self.assertIn("Choose a PostgreSQL data layout", result.stderr)
                for name in LAYOUTS:
                    self.assertIn(name, result.stderr)
                    self.assertFalse((self.stack / name).exists())

    def test_enabled_layouts_allow_compose(self):
        for layouts in ((LAYOUTS[0],), (LAYOUTS[1],), LAYOUTS):
            with self.subTest(layouts=layouts):
                for name in LAYOUTS:
                    (self.stack / name).unlink(missing_ok=True)
                self.log.unlink(missing_ok=True)
                for name in layouts:
                    # The hook only checks file existence, not its contents.
                    (self.stack / name).write_text("services: {}\n")
                result = self.run_upgrade("--no-up", str(self.stack), "config")
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertTrue(self.log.exists())


class DataLayoutComposeTests(unittest.TestCase):
    def test_postgres_requires_explicit_nonempty_tag(self):
        for tag in (None, ""):
            for overlays in ((), ("compose.build.yaml",)):
                with self.subTest(tag=tag, overlays=overlays):
                    with self.assertRaises(subprocess.CalledProcessError) as failure:
                        parse_compose("postgres", overlays, tag=tag)
                    self.assertIn("Set TAG explicitly", failure.exception.stderr)

    def test_postgres_explicit_tag_in_base_and_build(self):
        for overlays in ((), ("compose.build.yaml",)):
            with self.subTest(overlays=overlays):
                config = parse_compose("postgres", overlays, tag="17")
                service = config["services"]["postgres"]
                image = "localhost/build/postgres" if overlays else "postgres"
                self.assertEqual(service["image"], f"{image}:17")
                if overlays:
                    self.assertEqual(service["build"]["args"]["TAG"], "17")

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


class ExternalDatabaseTests(UpgradeTestCase):
    def test_sub2api_external_database_needs_no_layout_choice(self):
        config = parse_compose("sub2api", ())
        self.assertNotIn("postgres", config["services"])
        shutil.copytree(ROOT / "sub2api", self.stack, dirs_exist_ok=True)
        (self.stack / ".env").write_text("")
        result = self.run_upgrade("--no-up", str(self.stack), "config")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("Choose a PostgreSQL data layout", result.stderr)
        self.assertTrue(self.log.exists())


if __name__ == "__main__":
    unittest.main()
