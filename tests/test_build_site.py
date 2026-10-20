import sys
import unittest
import json
import tempfile
from datetime import date
from unittest.mock import patch
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


    def test_toss_first_second_choices(self):
        choices=b.split_toss_prizes("일등 부산 정통 어묵 꼬치 이등 통참깨 100% 참기름")
        self.assertEqual(choices,[("1등","부산 정통 어묵 꼬치"),("2등","통참깨 100% 참기름")])
        self.assertEqual(b.split_toss_prizes("일등만 있음"),[])
        self.assertEqual(b.split_toss_prizes("한가지 정답"),[])
        self.assertEqual(b.split_toss_prizes("1등 선택 A 2등 선택 B"),[("1등","선택 A"),("2등","선택 B")])

    def test_curate_missing_question_duplication(self):
        base={"app":"shinhanpay","date":"2026-10-20","source_url":"https://example.org/day","answer":"쿠팡와우 멤버십"}
        good=dict(base,id="good-record",question_hint="생활요금 자동납부 이벤트는?")
        bad=dict(base,id="bad-record",question_hint="문제 문구 확인 불가")
        self.assertEqual(b.curate_rows([bad,good]),[good])
        another=dict(base,id="other-record",question_hint="다른 문제도 같은 정답인가요?")
        self.assertEqual(len(b.curate_rows([good,another])),2)

    def test_build_app_search_saved_snapshots_and_menu(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            quiz=[{
              "id":"qb-1234test","app":"toss","app_name":"토스",
              "date":"2026-10-20","question_hint":"두근두근 1등 찍기 퀴즈",
              "answer":"일등 부산 정통 어묵 꼬치 이등 통참깨 100% 참기름",
              "time":None,"source_url":"https://example.org/toss",
            }]
            (root/"data.json").write_text(json.dumps({"quizzes":quiz},ensure_ascii=False),encoding="utf-8")
            (root/"catalog.json").write_text(json.dumps({"apps":[
              {"id":"toss","name":"토스","source_url":"https://example.org/toss"},
              {"id":"bitbunny","name":"비트버니 퀴즈","source_url":"https://example.org/bitbunny","feed":"link_only"}
            ]},ensure_ascii=False),encoding="utf-8")
            with patch.object(b,"SITE",root),patch.object(b,"TODAY",date(2026,10,20)):
                b.main()
            home=(root/"index.html").read_text(encoding="utf-8")
            detail=(root/"quiz/toss/2026-10-20/qb-1234test/index.html").read_text(encoding="utf-8")
            apps=(root/"apps/index.html").read_text(encoding="utf-8")
            self.assertNotIn("부산 정통 어묵",home)
            self.assertIn("1등 상품",detail)
            self.assertIn("2등 상품",detail)
            self.assertIn('data-copy-text="부산 정통 어묵 꼬치"',detail)
            self.assertIn('data-answer="일등 부산 정통 어묵 꼬치',detail)
            self.assertIn("비트버니 퀴즈",apps)
            self.assertIn("운영 확인 대기",apps)
            self.assertTrue((root/"menu/index.html").is_file())
            self.assertTrue((root/"challenge/index.html").is_file())
            challenge=(root/"challenge/index.html").read_text(encoding="utf-8")
            self.assertIn("금 0.1돈",challenge)
            self.assertIn("0.375g",challenge)
            self.assertIn("/quizpick-lite/assets/challenge.js",challenge)
            self.assertIn("5,000원",challenge)
            self.assertIn("10,000원",challenge)
            self.assertIn('href="/quizpick-lite/challenge/"',home)
            self.assertIn("/quizpick-lite/challenge/",(root/"sitemap.xml").read_text(encoding="utf-8"))
            published=json.loads((root/"active-quizzes.json").read_text(encoding="utf-8"))
            self.assertIn("/quizpick-lite/quiz/toss/2026-10-20/qb-1234test/",published["paths"])
            self.assertIn("menu/",home)
            self.assertIn("sitemap.xml",(root/"robots.txt").read_text(encoding="utf-8"))

    def test_service_icons_render_original_publisher_artwork(self):
        for app in b.APPS:
            icon = b.app_icon(app)
            self.assertIn('class="app-brand-logo"', icon)
            self.assertTrue(any(host in icon for host in ("static.toss.im", "m.kakaobank.com", "play-lh.googleusercontent.com")))
            self.assertIn('class="appicon-fallback"', icon)
            self.assertIn('width="64"', icon)
            self.assertIn("QUIZPICK", b.brand_strip(app))
        self.assertIn('class="app-brand-logo"', b.app_summary("toss", []))
        self.assertIn('data-app="toss"', b.app_summary("toss", []))

if __name__ == "__main__":
    unittest.main()
