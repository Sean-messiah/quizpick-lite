#!/usr/bin/env python3
"""Pull compact, source-linked public quiz references for two focus apps."""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from urllib.robotparser import RobotFileParser
import hashlib
import json
import re

import requests
from bs4 import BeautifulSoup
from collect import KST, OUTPUT, merge

HOST = "quizbells.com"
AGENT = "QuizPickLiteBot/0.2 (+https://sean-messiah.github.io/quizpick-lite/)"
FEEDS = (
    ("kakaobank", "카카오뱅크", "https://quizbells.com/quiz/kakaobank/weekly/answer"),
    ("toss", "토스", "https://quizbells.com/quiz/toss/weekly/answer"),
)

def parse_weekly_table(html, slug, app_name, source_url, today):
    """Read only dated question/answer table cells; ignore promotional prose."""
    soup = BeautifulSoup(html, "html.parser")
    year = datetime.strptime(today, "%Y-%m-%d").year
    min_day = (datetime.strptime(today, "%Y-%m-%d") - timedelta(days=6)).date()
    max_day = datetime.strptime(today, "%Y-%m-%d").date()
    rows = []
    seen = defaultdict(int)

    for table in soup.select("table"):
        heads = " ".join(th.get_text(" ", strip=True) for th in table.select("th"))
        if not all(word in heads for word in ("날짜", "문제", "정답")):
            continue
        active_day = None
        for tr in table.select("tr"):
            cols = tr.find_all("td", recursive=False)
            if len(cols) != 3:
                continue
            date_text = cols[0].get_text(" ", strip=True)
            date_match = re.search(r"(\d{1,2})월\s*(\d{1,2})일", date_text)
            if date_match:
                month, day = map(int, date_match.groups())
                candidate = datetime(year, month, day).date() if 1 <= month <= 12 and 1 <= day <= 28 else None
                if candidate is None:
                    try:
                        candidate = datetime(year, month, day).date()
                    except ValueError:
                        active_day = None
                        continue
                if candidate > max_day + timedelta(days=5):
                    candidate = datetime(year - 1, month, day).date()
                active_day = candidate
            if active_day is None or not (min_day <= active_day <= max_day):
                continue
            question = " ".join(cols[1].stripped_strings).strip()
            answer = " ".join(cols[2].stripped_strings).strip()
            if not question or not answer or answer in ("정답 보기", "확인 중", "미확정", "-") or len(answer) > 180:
                continue
            date = active_day.isoformat()
            key = (date, question)
            seen[key] += 1
            identity = f"{slug}|{date}|{question}|{seen[key]}"
            uid = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:16]
            clock = None
            if "아침 8시" in question:
                clock = "08:00"
            elif "점심 12시" in question:
                clock = "12:00"
            elif "저녁 8시" in question:
                clock = "20:00"
            rows.append({
                "id": "qb-" + uid, "app": slug, "app_name": app_name,
                "question_hint": question[:64] + ("…" if len(question) > 64 else ""),
                "answer": answer, "date": date, "time": clock,
                "source": "퀴즈벨 공개 자료", "source_url": source_url,
                "source_status": "진행 여부 미확인",
                "confidence_label": "외부 게시 정보 · 미검증",
            })
    return rows

def load_page(url):
    head = {"User-Agent": AGENT, "Accept": "text/html"}
    robots = requests.get(f"https://{HOST}/robots.txt", headers=head, timeout=12, allow_redirects=False)
    if robots.status_code != 200:
        raise RuntimeError(f"robots 상태 {robots.status_code}")
    parser = RobotFileParser()
    parser.parse(robots.text.splitlines())
    if not parser.can_fetch(AGENT, url):
        raise RuntimeError("robots 접근 불허")
    res = requests.get(url, headers=head, timeout=14, stream=True, allow_redirects=False)
    if res.status_code != 200:
        raise RuntimeError(f"수집 HTTP {res.status_code}")
    data = bytearray()
    for chunk in res.iter_content(32768):
        data.extend(chunk)
        if len(data) > 800_000:
            raise RuntimeError("응답이 너무 큼")
    return bytes(data).decode("utf-8", errors="replace")

def main():
    now = datetime.now(KST)
    today = now.date().isoformat()
    existing = json.loads(OUTPUT.read_text(encoding="utf-8"))
    additions = []
    for slug, name, url in FEEDS:
        try:
            records = parse_weekly_table(load_page(url), slug, name, url, today)
            print(f"{name}: {len(records)}건 수집")
            additions.extend(records)
        except (RuntimeError, requests.RequestException, OSError) as exc:
            print(f"SKIP {name}: {exc}")
    if not additions:
        print("카카오뱅크/토스 추가 자료 없음 — 기존 데이터 보존")
        return
    merged = merge(existing.get("quizzes", []), additions, today)
    if merged == existing.get("quizzes", []):
        print("변경 없음")
        return
    existing["quizzes"] = merged
    existing["updated_at"] = now.isoformat(timespec="seconds")
    existing["source_mode"] = "public-page"
    OUTPUT.write_text(json.dumps(existing, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"전체 저장: {len(merged)}건")

if __name__ == "__main__":
    main()
