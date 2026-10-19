import sys
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scraper"))
from collect import collect_dates, merge, get_app

class BackfillTests(unittest.TestCase):
    def test_last_seven_days(self):
        at=datetime(2026,10,19,12,0,tzinfo=timezone(timedelta(hours=9)))
        dates=collect_dates(at,7)
        self.assertEqual(dates[0], "2026-10-13")
        self.assertEqual(dates[-1], "2026-10-19")
        self.assertEqual(len(dates),7)
    def test_today_only(self):
        at=datetime(2026,10,19,12,0,tzinfo=timezone(timedelta(hours=9)))
        self.assertEqual(collect_dates(at,1),["2026-10-19"])
    def test_day_limit(self):
        with self.assertRaises(ValueError):
            collect_dates(datetime.now(timezone.utc),8)
    def test_app_mapping(self):
        self.assertEqual(get_app("KB Pay 오늘의 퀴즈")[0], "kbpay")
        self.assertEqual(get_app("캐시워크")[0], "cashwalk")
        self.assertEqual(get_app("카카오뱅크 AI 이모지 퀴즈")[0], "kakaobank")

if __name__ == "__main__":
    unittest.main()
