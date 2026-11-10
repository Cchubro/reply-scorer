#!/usr/bin/env python3
"""Tests for reply_scorer.py.

Real cases come from @Cchubro's Day 1-2 replies (see the goal daily log):
the best Day 2 reply should SHIP, empty praise should REWRITE.
Run: python -m unittest test_reply_scorer.py -v
"""

import unittest

from reply_scorer import score, x_length

# Best Day 2 reply, verbatim from the daily log (to @0xWhitemon, 2026-11-09):
BEST_DAY2 = (
    "迴圈本身不難，難的是停下來的條件。三個 agent 互相點頭還是可能一起錯，"
    "真正的關鍵是獨立驗證：能跑的檢查、不是自己評自己。沒有這一層，"
    "迴圈只是比較久的失敗。"
)
BEST_DAY2_POST = (
    "Don't let the same agent build and review its own work. "
    "Multi-agent loops need independent verification — harness engineering."
)


class TestVerdicts(unittest.TestCase):
    def test_best_day2_reply_ships(self):
        result = score(BEST_DAY2, BEST_DAY2_POST)
        self.assertEqual(result["verdict"], "SHIP")
        self.assertGreaterEqual(result["score"], 70)

    def test_generic_praise_rewrites(self):
        for draft in [
            "Great post! So true 🔥",
            "This is amazing, love this!",
            "说得太好了，学习了！",
            "100% facts 🙌",
        ]:
            with self.subTest(draft=draft):
                result = score(draft)
                self.assertEqual(result["verdict"], "REWRITE")
                self.assertLess(result["score"], 40)

    def test_mid_reply_with_sharp_question_improves(self):
        result = score(
            "Good point about evals — how do you catch flaky tests "
            "before they poison the whole suite?"
        )
        self.assertEqual(result["verdict"], "IMPROVE")
        self.assertGreaterEqual(result["score"], 35)

    def test_empty_draft_scores_zero(self):
        result = score("   ")
        self.assertEqual(result["score"], 0)
        self.assertEqual(result["verdict"], "REWRITE")

    def test_specific_counterpoint_ships(self):
        result = score(
            "Disagree — 3 agents agreeing is not verification. The key is "
            "an independent check that can fail: run the tests, don't ask "
            "the builder to grade itself."
        )
        self.assertEqual(result["verdict"], "SHIP")

    def test_filler_gets_flagged(self):
        result = score(
            "In today's fast-paced AI landscape, it's important to note "
            "that this game-changer will supercharge your workflow."
        )
        self.assertLess(result["checks"]["clean"]["points"], 0)
        self.assertEqual(result["verdict"], "REWRITE")

    def test_overlong_draft_flagged(self):
        draft = ("Independent verification matters more than model choice. " * 8).strip()
        result = score(draft)
        self.assertGreater(result["length"], 280)
        self.assertLess(result["checks"]["length"]["points"], 0)

    def test_post_overlap_bonus(self):
        post = "Multi-agent loops need independent verification."
        with_post = score("Independent verification is the whole game — "
                          "without it the loop just fails slower.", post)
        without_post = score("Independent verification is the whole game — "
                             "without it the loop just fails slower.")
        self.assertGreater(with_post["checks"]["specificity"]["points"],
                           without_post["checks"]["specificity"]["points"])

    def test_no_overlap_with_post_flagged(self):
        result = score("Great insights on shipping fast!",
                       "Multi-agent loops need independent verification.")
        self.assertIn("Doesn't reference anything", " ".join(result["fixes"]))

    def test_generic_question_gets_no_value(self):
        result = score("Interesting take on evals. What do you think?")
        self.assertEqual(result["checks"]["value"]["points"], 0)

    def test_score_always_in_range(self):
        for draft in ["x", "Great post!", BEST_DAY2, "a " * 200]:
            self.assertTrue(0 <= score(draft)["score"] <= 100)


class TestXLength(unittest.TestCase):
    def test_link_counts_23(self):
        self.assertEqual(x_length("see https://example.com/a/very/long/path here"), 4 + 23 + 5)

    def test_plain_text_unchanged(self):
        self.assertEqual(x_length("hello world"), 11)


if __name__ == "__main__":
    unittest.main()
