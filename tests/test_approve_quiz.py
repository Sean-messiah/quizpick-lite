import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from approve_quiz import approve, candidates

class PushApprovalTests(unittest.TestCase):
    def setUp(self):
        self.quiz = {
            "id":"qb-verify001","app":"toss","date":"2026-10-24",
            "time":"12:00","answer":"정답가","question_hint":"어떤 물건을 고르나요?",
            "source_url":"https://example.org/quiz/2026-10-24"
        }
        self.feed={"quizzes":[self.quiz]}
        self.curated={"schema_version":1,"quizzes":[]}

    def approve(self, **changes):
        args=dict(feed=self.feed,curated=self.curated,quiz_id=self.quiz["id"],
                  expected_answer=self.quiz["answer"],verification="checked_original_app",
                  confirmation="APPROVE",today=self.quiz["date"])
        args.update(changes)
        return approve(**args)

    def test_no_automatic_approval_without_explicit_evidence(self):
        for confirmation,method in [("LIST_ONLY","checked_original_app"),("APPROVE","not_checked")]:
            with self.assertRaises(ValueError):
                self.approve(confirmation=confirmation, verification=method)

    def test_approval_preserves_source_and_marks_review_time(self):
        feed,q=self.approve()
        self.assertEqual(q["answer"],"정답가")
        self.assertEqual(q["source_url"],self.quiz["source_url"])
        self.assertEqual(q["verification_method"],"checked_original_app")
        self.assertEqual(q["reward_status"],"NOT_CHECKED")
        self.assertTrue(q["reviewed"])
        self.assertIn("+09:00",q["reviewed_at_kst"])
        self.assertEqual(len(feed["quizzes"]),1)
        self.assertEqual(len(self.curated["quizzes"]),0)

    def test_stale_or_wrong_answer_never_approves(self):
        with self.assertRaises(ValueError):
            self.approve(expected_answer="전혀 다른 정답")
        with self.assertRaises(ValueError):
            self.approve(today="2026-10-25")

    def test_duplicate_approval_rejected(self):
        feed,q=self.approve()
        with self.assertRaises(ValueError):
            self.approve(curated=feed)

    def test_candidate_list_is_today_only(self):
        self.assertEqual(len(candidates(self.feed,"2026-10-24")),1)
        self.assertEqual(len(candidates(self.feed,"2026-10-23")),0)

    def test_invalid_sources_rejected(self):
        self.feed["quizzes"][0]["source_url"]="http://example.org/quiz"
        with self.assertRaises(ValueError):
            self.approve()

if __name__ == "__main__":
    unittest.main()
