import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scraper"))
from collect_focus import parse_weekly_table

HTML = """<html><main><table><thead><tr><th>날짜</th><th>문제</th><th>정답</th></tr></thead><tbody>
<tr><td>10월 18일 (일)</td><td>AI 이모지 퀴즈 (아침 8시)</td><td><p>해바라기씨</p></td></tr>
<tr><td></td><td>AI 이모지 퀴즈 (점심 12시)</td><td><p>레스토랑</p></td></tr>
<tr><td>10월 17일 (토)</td><td>AI 이모지 퀴즈 (저녁 8시)</td><td><p>예언</p></td></tr>
</tbody></table></main></html>"""

class FocusTests(unittest.TestCase):
    def test_table_date_inherits(self):
        result = parse_weekly_table(HTML, "kakaobank", "카카오뱅크", "https://quizbells.com/quiz/kakaobank/weekly/answer", "2026-10-19")
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0]["answer"], "해바라기씨")
        self.assertEqual(result[1]["date"], "2026-10-18")
        self.assertEqual(result[1]["time"], "12:00")
    def test_expiry_filter(self):
        result = parse_weekly_table(HTML, "toss", "토스", "https://quizbells.com/quiz/toss/weekly/answer", "2026-11-01")
        self.assertEqual(result, [])

if __name__ == "__main__":
    unittest.main()
