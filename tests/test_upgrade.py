"""Regressions for upgrade argument parsing and forwarding."""
import unittest

from support import UpgradeTestCase


class UpgradeTests(UpgradeTestCase):
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
