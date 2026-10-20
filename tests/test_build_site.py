import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import build_site as b

class BuildSiteTests(unittest.TestCase):
    def test_priority_apps(self):
        self.assertEqual(b.APPS["toss"][0], "토스")
        self.assertEqual(b.APPS["kakaobank"][0], "카카오뱅크")
    def test_route_paths_with_github_pages_prefix(self):
        self.assertEqual(b.local(), "/quizpick-lite/")
        self.assertEqual(b.app_path("toss"), "/quizpick-lite/toss/")
        self.assertEqual(b.app_path("cashwalk"), "/quizpick-lite/apps/cashwalk/")
    def test_html_escapes_untrusted_question(self):
        self.assertEqual(b.e('<script>alert("x")</script>'), '&lt;script&gt;alert(&quot;x&quot;)&lt;/script&gt;')
    def test_answer_only_on_detail(self):
        q = {"id":"salbopick-test123", "app":"cashwalk", "date":"2026-10-20",
             "question_hint":"샘플 문제?", "answer":"SECRET_ANSWER", "time":"12:30"}
        self.assertNotIn("SECRET_ANSWER", b.item_card(q))
        self.assertIn("/quiz/cashwalk/2026-10-20/salbopick-test123/", b.item_card(q))
    def test_google_analytics_and_navigation(self):
        p=b.page("테스트","설명","<p>hello</p>",b.local())
        self.assertIn("G-3Y68828WYZ",p)
        self.assertIn('rel="canonical"',p)
        self.assertIn('name="viewport"',p)
    def test_noindex_detail(self):
        self.assertIn('noindex,follow',b.page("제목","설명","",b.local("toss"),noindex=True))

if __name__ == "__main__":
    unittest.main()
