"""No-network tests for daily Instagram publication reservation and retry safety."""
import importlib
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

# daily.py imports generate for image rendering. The reservation path needs no Pillow.
mock_generate = types.ModuleType("generate")
mock_generate.ROOT = Path(".")
mock_generate.load_content = lambda: {}
mock_generate.render = lambda *args, **kwargs: None
with patch.dict(sys.modules, {"generate": mock_generate}):
    daily = importlib.import_module("scripts.daily")


class DailyPublishTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "posts").mkdir()
        self.day = "2026-11-08"
        self.state = self.root / "posts/state.json"
        self.state.write_text(json.dumps({"next_index": 0, "history": [
            {"date": self.day, "title": "New daily post"}
        ]}), encoding="utf-8")
        self.env = patch.dict("os.environ", {"GITHUB_RUN_ID": "1234", "GITHUB_RUN_ATTEMPT": "1",
                                             "IG_ACCESS_TOKEN": "fake", "IMAGE_BASE_URL": "https://example.invalid"})
        self.env.start()
        self.addCleanup(self.env.stop)
        self.patcher = patch.multiple(daily, TODAY=self.day, STATE=self.state, POSTS=self.root / "posts")
        self.patcher.start()
        self.addCleanup(self.patcher.stop)

    def test_second_reservation_fails_closed(self):
        daily.reserve_publish()
        with self.assertRaisesRegex(RuntimeError, "Prior publish attempt"):
            daily.reserve_publish()
        self.assertEqual(json.loads(self.state.read_text())["history"][0]["publish_state"], "pending")

    def test_missing_reservation_does_not_call_api(self):
        (self.root / "posts" / f"{self.day}.json").write_text(json.dumps({"full_caption": "hello"}))
        with patch.object(daily, "http_json", side_effect=AssertionError("No API calls allowed")):
            with self.assertRaisesRegex(RuntimeError, "reservation missing"):
                daily.publish()

    def test_reserved_publish_records_media_id(self):
        (self.root / "posts" / f"{self.day}.json").write_text(json.dumps({"full_caption": "hello"}))
        daily.reserve_publish()
        with patch.object(daily, "http_json", side_effect=[{"id": "container"}, {"status_code": "FINISHED"}, {"id": "ig-media"}]):
            daily.publish()
        entry = json.loads(self.state.read_text())["history"][0]
        self.assertEqual(entry["media_id"], "ig-media")
        self.assertEqual(entry["publish_state"], "published")


if __name__ == "__main__":
    unittest.main()
