import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1] / "scraper"))
from collect_expanded import APPS, parse_monthly

HTML = """<html><body>
<h2>10월 19일 정답 2건</h2><ul>
<li>오전 12:05<p class="a-q">처음 문제의 핵심은 무엇일까요?</p>정답: 시작</li>
<li>오후 01:03<p class="a-q">두 번째 퀴즈 답?</p>정답: 정답2</li>
</ul>
<h2>10월 18일 정답 1건</h2><ul><li>오전 03:00<p class="a-q">전날 문제는?</p>정답: 어제</li></ul>
</body></html>"""

class ExpandedTests(unittest.TestCase):
    def test_monthly_with_multiple_days(self):
        rows = parse_monthly(HTML,"cashwalk","캐시워크","cashwalk","https://quiz.jjyu.co.kr/quiz/cashwalk/monthly/","2026-10-19")
        self.assertEqual(len(rows),3)
        self.assertEqual(rows[0]["answer"],"시작")
        self.assertEqual(rows[1]["time"],"13:03")
        self.assertEqual(rows[2]["date"],"2026-10-18")
    def test_no_future_data(self):
        rows = parse_monthly(HTML,"cashwalk","캐시워크","cashwalk","https://quiz.jjyu.co.kr/quiz/cashwalk/monthly/","2026-10-16")
        self.assertEqual(rows,[])
    def test_source_count(self):
        self.assertGreaterEqual(len(APPS), 30)

if __name__=="__main__":
    unittest.main()
