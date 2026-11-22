"""No-network checks for scheduled and manual Instagram publishing keys."""
import runpy
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "daily.py"

class ManualScheduleSeparationTests(unittest.TestCase):
    def load_key(self, event, run_id):
        fake = types.ModuleType("generate")
        fake.ROOT = ROOT
        fake.load_content = lambda: {}
        fake.render = lambda *args, **kwargs: None
        with patch.dict(sys.modules, {"generate": fake}), patch.dict(
            "os.environ", {"GITHUB_EVENT_NAME": event, "GITHUB_RUN_ID": run_id}
        ):
            data = runpy.run_path(str(SCRIPT))
        return data["TODAY"], data["CALENDAR_DAY"]

    def test_scheduled_key_is_calendar_day(self):
        key, day = self.load_key("schedule", "777")
        self.assertEqual(key, day)

    def test_manual_key_is_separate_and_run_specific(self):
        first, day = self.load_key("workflow_dispatch", "777")
        second, _ = self.load_key("workflow_dispatch", "778")
        self.assertEqual(first, f"manual-{day}-777")
        self.assertNotEqual(first, second)
        self.assertNotEqual(first, day)

if __name__ == "__main__":
    unittest.main()
