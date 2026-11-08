"""Offline guards for Instagram publishing and schedule state."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class WorkflowIsolationTests(unittest.TestCase):
    def test_publish_receipt_is_persisted_before_notifications(self):
        workflow = (ROOT / ".github/workflows/daily-post.yml").read_text(encoding="utf-8")
        self.assertLess(workflow.index("Paylaşım kimliğini hemen kaydet"), workflow.index("E-posta gönder"))
        self.assertIn("git add posts/state.json", workflow)

    def test_manual_dispatch_does_not_write_daily_marker(self):
        workflow = (ROOT / ".github/workflows/daily-post.yml").read_text(encoding="utf-8")
        self.assertIn('if [ "${{ github.event_name }}" = "schedule" ]; then\n            TZ=Europe/Istanbul date +%F > .gunluk-son', workflow)

if __name__ == "__main__":
    unittest.main()
