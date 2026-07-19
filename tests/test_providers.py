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
        self.assertEqual(self.provider.execution_mode, "target_container")
        self.assertTrue(self.provider.requires_docker_socket)

    def test_builds_targeted_machine_readable_command(self):
        command = self.provider.managed_prefill_command(730)
        self.assertIn("prefill 730", command)
        self.assertIn("--verbose", command)
        self.assertIn("--no-ansi", command)


class EmbeddedSteamProviderTests(unittest.TestCase):
    def setUp(self):
        self.provider = create_provider(
            "embedded-steam",
            working_directory="/config/steam-engine",
            container_user="",
            command="/opt/steamprefill/SteamPrefill prefill",
            embedded_binary="/opt/steamprefill/SteamPrefill",
        )

    def test_runs_locally_without_docker_socket(self):
        self.assertEqual(self.provider.execution_mode, "local")
        self.assertFalse(self.provider.requires_docker_socket)
        self.assertFalse(self.provider.compatibility_mode)
        self.assertIn("/opt/steamprefill/SteamPrefill select-apps", self.provider.select_games_command)

    def test_builds_targeted_command_with_machine_readable_flags(self):
        command = self.provider.managed_prefill_command(730)
        self.assertIn("prefill 730", command)
        self.assertIn("--verbose", command)
        self.assertIn("--no-ansi", command)

    def test_unknown_provider_is_rejected(self):
        with self.assertRaises(ValueError):
            create_provider(
                "not-a-provider",
                working_directory="/tmp",
                container_user="",
                command="ignored",
            )


if __name__ == "__main__":
    unittest.main()

class EmbeddedUpgradeAliasTests(unittest.TestCase):
    def test_v07_default_variables_are_migrated_to_embedded_paths(self) -> None:
        import json
        import os
        import subprocess
        import sys
        import tempfile

        with tempfile.TemporaryDirectory() as directory:
            engine_dir = f"{directory}/steam-engine"
            environment = os.environ.copy()
            environment.update(
                {
                    "CACHEDECK_PROVIDER": "embedded-steam",
                    "CACHEDECK_CONFIG_DIR": directory,
                    "CACHEDECK_STEAM_ENGINE_DIR": engine_dir,
                    "PREFILL_DIR": "/lancacheprefill/SteamPrefill",
                    "PREFILL_USER": "prefill",
                    "PREFILL_STATE_DIR": "/tmp/cachedeck",
                    "PREFILL_COMMAND": "./SteamPrefill prefill",
                }
            )
            result = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    (
                        "import json, app.main as m; "
                        "print(json.dumps([m.PREFILL_DIR, m.PREFILL_USER, "
                        "m.PREFILL_STATE_DIR, m.PREFILL_COMMAND]))"
                    ),
                ],
                capture_output=True,
                text=True,
                check=True,
                env=environment,
            )
            values = json.loads(result.stdout)

        self.assertEqual(values[0], engine_dir)
        self.assertEqual(values[1], "")
        self.assertEqual(values[2], f"{engine_dir}/state")
        self.assertEqual(values[3], f"{engine_dir}/SteamPrefill prefill")
