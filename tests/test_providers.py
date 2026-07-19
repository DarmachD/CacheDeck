import unittest

from app.providers import create_provider


class SteamPrefillProviderTests(unittest.TestCase):
    def setUp(self):
        self.provider = create_provider(
            "steamprefill",
            working_directory="/lancacheprefill/SteamPrefill",
            container_user="prefill",
            command="./SteamPrefill prefill",
        )

    def test_exposes_foundation_capabilities_honestly(self):
        capabilities = self.provider.capabilities
        self.assertTrue(capabilities.per_app_jobs)
        self.assertFalse(capabilities.structured_progress)
        self.assertFalse(capabilities.manifest_tracking)
        self.assertFalse(capabilities.per_game_purge)

    def test_builds_targeted_machine_readable_command(self):
        command = self.provider.managed_prefill_command(730)
        self.assertIn("prefill 730", command)
        self.assertIn("--verbose", command)
        self.assertIn("--no-ansi", command)

    def test_rejects_unavailable_native_provider(self):
        with self.assertRaises(ValueError):
            create_provider(
                "native-steam",
                working_directory="/tmp",
                container_user="prefill",
                command="ignored",
            )


if __name__ == "__main__":
    unittest.main()
