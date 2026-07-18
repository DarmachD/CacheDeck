import unittest

from app.main import managed_prefill_command


class MainHelperTests(unittest.TestCase):
    def test_managed_prefill_adds_machine_readable_flags(self):
        command = managed_prefill_command(730)
        self.assertIn("prefill 730", command)
        self.assertIn("--verbose", command)
        self.assertIn("--no-ansi", command)

    def test_managed_prefill_does_not_duplicate_flags(self):
        command = managed_prefill_command()
        self.assertEqual(command.split().count("--verbose"), 1)
        self.assertEqual(command.split().count("--no-ansi"), 1)


if __name__ == "__main__":
    unittest.main()
