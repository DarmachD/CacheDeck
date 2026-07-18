import tempfile
import unittest
from pathlib import Path

from app.library import (
    GameQueueItem,
    LibraryStore,
    QueueStore,
    SelectedApp,
    output_indicates_successful_prefill,
    parse_progress_snapshot,
    parse_selected_apps_status,
)


class LibraryParserTests(unittest.TestCase):
    def test_parses_box_table(self):
        output = """
│ App ID  │ App                                    │ Download Size │
│ 1466860 │ Age of Empires IV: Anniversary Edition │ 55.0 GiB      │
│ 730     │ Counter-Strike 2                       │ 34.4 GiB      │
"""
        apps = parse_selected_apps_status(output)
        self.assertEqual([app.app_id for app in apps], [1466860, 730])
        self.assertEqual(apps[0].name, "Age of Empires IV: Anniversary Edition")
        self.assertEqual(apps[0].download_size, "55.0 GiB")

    def test_parses_plain_status_rows(self):
        output = """
Age of Empires IV: Anniversary Edition    55.0 GiB
Counter-Strike 2                           34.4 GiB
"""
        apps = parse_selected_apps_status(output)
        self.assertEqual(len(apps), 2)
        self.assertEqual(apps[1].name, "Counter-Strike 2")

    def test_recognises_successful_prefill_summary(self):
        output = """
Prefilled 288 apps in 01:23:45
Updated | Up To Date
      12 |        276
"""
        self.assertTrue(output_indicates_successful_prefill(output))
        self.assertFalse(output_indicates_successful_prefill("Steam login failed"))

    def test_parses_live_progress(self):
        output = """
[1:13:11 AM] Starting Age of Empires IV: Anniversary Edition
Downloading.. 35% 10:46:33 19.7 / 55.0 GiB 7.8 Mbit/s
"""
        progress = parse_progress_snapshot(output)
        self.assertEqual(progress.app_name, "Age of Empires IV: Anniversary Edition")
        self.assertEqual(progress.progress, 35.0)
        self.assertEqual(progress.downloaded, "19.7 GiB")
        self.assertEqual(progress.total, "55.0 GiB")
        self.assertEqual(progress.speed, "7.8 Mbit/s")


class StoreTests(unittest.TestCase):
    def test_library_state_survives_refresh(self):
        with tempfile.TemporaryDirectory() as directory:
            store = LibraryStore(Path(directory) / "library.json")
            store.replace_selected(
                [SelectedApp(app_id=730, name="Counter-Strike 2", download_size="34.4 GiB")],
                "2026-07-18T00:00:00+00:00",
            )
            store.update_by_app_id(730, status="downloaded", progress=100.0)
            games = store.replace_selected(
                [SelectedApp(app_id=730, name="Counter-Strike 2", download_size="35.0 GiB")],
                "2026-07-18T01:00:00+00:00",
            )
            self.assertEqual(games[0].status, "downloaded")
            self.assertEqual(games[0].download_size, "35.0 GiB")

    def test_known_app_id_gets_artwork_without_lookup(self):
        with tempfile.TemporaryDirectory() as directory:
            store = LibraryStore(Path(directory) / "library.json")
            games = store.replace_selected(
                [SelectedApp(app_id=730, name="Counter-Strike 2", download_size="34.4 GiB")],
                "2026-07-18T00:00:00+00:00",
            )
            self.assertIn("/730/header.jpg", games[0].image_url or "")
            self.assertEqual(games[0].store_url, "https://store.steampowered.com/app/730/")

    def test_queue_deduplicates_active_game(self):
        with tempfile.TemporaryDirectory() as directory:
            queue = QueueStore(Path(directory) / "queue.json")
            first = queue.enqueue(
                GameQueueItem(
                    queue_id="a",
                    app_id=730,
                    app_name="Counter-Strike 2",
                    requested_at="2026-07-18T00:00:00+00:00",
                )
            )
            second = queue.enqueue(
                GameQueueItem(
                    queue_id="b",
                    app_id=730,
                    app_name="Counter-Strike 2",
                    requested_at="2026-07-18T00:01:00+00:00",
                )
            )
            self.assertEqual(first.queue_id, second.queue_id)
            self.assertEqual(len(queue.list()), 1)


if __name__ == "__main__":
    unittest.main()
