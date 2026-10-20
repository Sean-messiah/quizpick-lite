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
    def test_static_files_have_no_trailing_slash(self):
        self.assertEqual(b.static_url("assets", "style.css"), "/quizpick-lite/assets/style.css")
        self.assertEqual(b.static_url("assets", "app.js"), "/quizpick-lite/assets/app.js")
        self.assertEqual(b.static_url("sitemap.xml"), "/quizpick-lite/sitemap.xml")
        p = b.page("제목", "설명", "", b.local())
        self.assertIn('href="/quizpick-lite/assets/style.css"', p)
        self.assertIn('src="/quizpick-lite/assets/app.js"', p)
        self.assertNotIn('style.css/"', p)
        self.assertNotIn('app.js/"', p)

    def test_noindex_detail(self):
        self.assertIn('noindex,follow',b.page("제목","설명","",b.local("toss"),noindex=True))


    def test_pink_ui_routes_and_navigation(self):
        html = b.page("핑크 시안", "테스트 설명", "<p>body</p>", b.local())
        self.assertIn('content="#fff1f7"', html)
        self.assertIn('class="wordmark"', html)
        self.assertIn('class="mobile-nav"', html)
        self.assertIn('href="/quizpick-lite/saved/"', html)
        self.assertIn('href="/quizpick-lite/contact/"', html)
        self.assertIn('href="/quizpick-lite/assets/style.css"', html)

    def test_featured_app_cards_keep_answers_hidden(self):
        example = {"date": "2026-10-20", "answer": "SENSITIVE_ANSWER"}
        html = b.app_summary("toss", [example])
        self.assertIn('data-app="toss"', html)
        self.assertIn("회차별 정답 확인하기", html)
        self.assertNotIn("SENSITIVE_ANSWER", html)

if __name__ == "__main__":
    unittest.main()
