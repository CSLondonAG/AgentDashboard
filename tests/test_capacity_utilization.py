import ast
import unittest
from pathlib import Path
from typing import List, Optional, Tuple

import pandas as pd


def _load_helpers():
    source_path = Path(__file__).resolve().parents[1] / "app.py"
    tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
    wanted = {
        "merge_intervals",
        "clip_to_window",
        "sum_seconds",
        "intersect_seconds",
        "concurrent_slot_seconds",
        "email_assignable_capacity",
    }
    functions = [
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name in wanted
    ]
    namespace = {
        "pd": pd,
        "List": List,
        "Optional": Optional,
        "Tuple": Tuple,
        "Interval": Tuple[pd.Timestamp, pd.Timestamp],
        "CHAT_CONCURRENCY_CAPACITY": 2,
    }
    exec(compile(ast.Module(body=functions, type_ignores=[]), str(source_path), "exec"), namespace)
    return namespace


HELPERS = _load_helpers()
concurrent_slot_seconds = HELPERS["concurrent_slot_seconds"]
email_assignable_capacity = HELPERS["email_assignable_capacity"]


class CapacityUtilizationTests(unittest.TestCase):
    def setUp(self):
        self.start = pd.Timestamp("2026-10-20 09:00:00")
        self.end = self.start + pd.Timedelta(hours=1)
        self.available = [(self.start, self.end)]

    def test_one_chat_uses_half_capacity(self):
        slots = concurrent_slot_seconds(
            [(self.start, self.end)], self.available, capacity=2
        )
        self.assertEqual(slots / 2 / 3600, 0.5)

    def test_two_chats_use_full_capacity(self):
        slots = concurrent_slot_seconds(
            [(self.start, self.end)] * 2, self.available, capacity=2
        )
        self.assertEqual(slots / 2 / 3600, 1.0)

    def test_more_than_two_chats_is_capped(self):
        slots = concurrent_slot_seconds(
            [(self.start, self.end)] * 3, self.available, capacity=2
        )
        self.assertEqual(slots / 2 / 3600, 1.0)

    def test_email_is_assignable_without_chat(self):
        capacity, used, excess = email_assignable_capacity(
            [], [(self.start, self.end)], self.available
        )
        self.assertEqual((capacity, used, excess), (3600.0, 3600.0, 0.0))

    def test_any_chat_blocks_email_assignment(self):
        capacity, used, excess = email_assignable_capacity(
            [(self.start, self.end)], [(self.start, self.end)], self.available
        )
        self.assertEqual((capacity, used, excess), (0.0, 0.0, 3600.0))

    def test_only_chat_free_shared_time_counts_for_email(self):
        midpoint = self.start + pd.Timedelta(minutes=30)
        capacity, used, excess = email_assignable_capacity(
            [(self.start, midpoint)], [(self.start, self.end)], self.available
        )
        self.assertEqual((capacity, used, excess), (1800.0, 1800.0, 1800.0))


if __name__ == "__main__":
    unittest.main()
