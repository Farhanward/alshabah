from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from alshabah.batch import evaluate
from alshabah.datasets import convert_bitext
from alshabah.planner import plan_task, save_policy


class AlShabahTests(unittest.TestCase):
    def test_blocks_unapproved_domain(self):
        result = plan_task("contact support", url="https://evil.example", policy={"allowed_domains": ["carbonflows.store"], "dry_run": True})
        self.assertFalse(result["allowed"])

    def test_plans_contact_dry_run(self):
        result = plan_task("contact support", url="https://carbonflows.store")
        self.assertTrue(result["allowed"])
        self.assertTrue(result["dry_run"])
        self.assertGreaterEqual(len(result["steps"]), 3)

    def test_convert_and_batch_fixture(self):
        with tempfile.TemporaryDirectory(dir="C:/Projects") as tmp:
            src = Path(tmp) / "bitext.jsonl"
            out = Path(tmp) / "tasks.jsonl"
            policy = Path(tmp) / "policy.json"
            src.write_text('{"instruction":"contact support","intent":"contact"}\n', encoding="utf-8")
            save_policy(policy)
            convert_bitext(src, out)
            summary = evaluate(out, policy)
            self.assertEqual(summary["errors"], 0)
            self.assertEqual(summary["blocked"], 0)


if __name__ == "__main__":
    unittest.main()

