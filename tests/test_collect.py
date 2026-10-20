import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scraper"))
from collect import get_app, merge, parse_quizzes

HTML = """
<html><body><main>
<article><div>01:00 신한 쏠퀴즈 마감 신한카드(신한SOL페이) 퀴즈팡팡</div>
<h3>오늘 혜택 내용은 무엇인가요?</h3><p>정답 <strong>포인트 5000</strong></p></article>
<article><div>15:00 캐시워크 마감</div>
<h3>행사가 OO원에 들어갈 값은 무엇인가요?</h3><p>정답 <strong>13900</strong></p></article>
</main></body></html>
"""

class CollectionTests(unittest.TestCase):
    def test_parse_two_answers(self):
        data = parse_quizzes(HTML, "https://salbopick.com/today/quiz/date/2026-10-18", "2026-10-18")
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["answer"], "포인트 5000")
        self.assertEqual(data[1]["answer"], "13900")
    def test_classifies_specific_app(self):
        self.assertEqual(get_app("신한카드 SOL페이")[0], "shinhanpay")
        self.assertEqual(get_app("KB스타뱅킹 스타퀴즈")[0], "kbstar")
    def test_incomplete_question_duplicate_is_removed(self):
        complete={"id":"good","app":"shinhanpay","date":"2026-10-20",
                  "source_url":"https://source.example/day","answer":"예시",
                  "question_hint":"해당 이벤트의 대상은?"}
        incomplete=dict(complete,id="incomplete",question_hint="문제 문구 확인 불가")
        from collect import merge
        result=merge([incomplete,complete],[],"2026-10-20")
        self.assertEqual(result,[complete])

    def test_old_entries_filtered_and_deduplicated(self):
        live = parse_quizzes(HTML, "https://salbopick.com/today/quiz/date/2026-10-18", "2026-10-18")
        self.assertEqual(len(merge(live, live, "2026-10-18")), 2)
        self.assertEqual(len(merge(live, [], "2026-10-26")), 0)

if __name__ == "__main__":
    unittest.main()
