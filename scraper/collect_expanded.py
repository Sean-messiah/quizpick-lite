#!/usr/bin/env python3
"""Best-effort public quiz snippets from date-grouped monthly index pages.

This crawler respects robots.txt, caps requests and stores only compact,
source-linked question identifiers and short factual answers.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from hashlib import sha256
from pathlib import Path
from urllib.robotparser import RobotFileParser
import json
import re
import time

import requests
from bs4 import BeautifulSoup
from collect import KST, OUTPUT, merge

HOST = "quiz.jjyu.co.kr"
BASE = f"https://{HOST}/quiz"
AGENT = "QuizPickLiteBot/0.3 (+https://sean-messiah.github.io/quizpick-lite/)"
TIMEOUT = 12
MAX_BYTES = 620000
# Toss and KakaoBank AI remain in the earlier low-frequency collector.
APPS = [
    ("cashwalk", "캐시워크", "cashwalk"),
    ("shinhan-sol", "신한 쏠퀴즈", "shinhanbank"),
    ("kakaobank-ox", "카카오뱅크 OX", "kakaobank-ox"),
    ("ok-cashbag", "OK캐쉬백 오퀴즈", "okcashbag"),
    ("kbpay", "KB Pay", "kbpay"),
    ("cashdoc", "캐시닥·타임스프레드", "cashdoc"),
    ("climate-action", "기후행동 퀴즈", "climate"),
    ("hpoint", "H.Point", "hpoint"),
    ("bitbunny", "비트버니", "bitbunny"),
    ("kakaopay", "카카오페이", "kakaopay"),
    ("nh-allone", "NH올원뱅크", "nh"),
    ("kb-star", "KB스타뱅킹", "kbstar"),
    ("kbank", "케이뱅크", "kbank"),
    ("hana-onq", "하나원큐", "hanabank"),
    ("hana-life", "하나 금융생활 OX", "hana-life"),
    ("hana-travel", "하나 트래블미션", "hana-travel"),
    ("monimo", "모니모", "monimo"),
    ("monimo-eng", "모니모 영어", "monimo-eng"),
    ("paybooc", "페이북", "paybooc"),
    ("mydoctor", "나만의닥터", "mydoctor"),
    ("skstoa", "SK스토아", "skstoa"),
    ("auction", "옥션", "auction"),
    ("myhomeplus", "마이홈플러스", "myhomeplus"),
    ("syrup", "시럽 타임어택", "syrup"),
    ("doctornow", "닥터나우", "doctornow"),
    ("buzzvil", "버즈빌", "buzzvil"),
    ("harim-real", "하림더리얼", "harim-real"),
    ("woori-festa", "우리금융", "woori-festa"),
    ("bitbunny-ox", "비트버니 OX", "bitbunny-ox"),
    ("adapter", "어댑터", "adapter"),
    ("moneywalk", "머니워크", "moneywalk"),
    ("yoit", "요잇", "yoit"),
    ("yes24", "예스24", "yes24"),
    ("fallcent", "폴센트", "fallcent"),
    ("naverpay", "네이버페이", "naverpay"),
]

def parse_monthly(html, remote_slug, label, slug, url, today):
    soup = BeautifulSoup(html, "html.parser")
    max_date = datetime.strptime(today, "%Y-%m-%d").date()
    min_date = max_date - timedelta(days=6)
    records = []
    per_day = {}
    for heading in soup.find_all("h2"):
        txt = heading.get_text(" ", strip=True)
        m = re.search(r"(\d{1,2})월\s*(\d{1,2})일\s*정답", txt)
        if not m:
            continue
        month, day = map(int, m.groups())
        try:
            date = datetime(max_date.year, month, day).date()
        except ValueError:
            continue
        if date > max_date:
            date = datetime(max_date.year - 1, month, day).date()
        if not min_date <= date <= max_date:
            continue
        ul = heading.find_next_sibling("ul")
        if ul is None:
            continue
        for li in ul.find_all("li", recursive=False):
            if per_day.get(date, 0) >= 4:
                break
            question_tag = li.select_one(".a-q")
            if question_tag is None:
                continue
            question = question_tag.get_text(" ", strip=True).strip()
            raw = li.get_text(" ", strip=True)
            m_answer = re.search(r"정답\s*[:：]\s*(.+)$", raw)
            if not m_answer or not question:
                continue
            answer = m_answer.group(1).strip()
            if not 1 <= len(answer) <= 90 or "정답 확인" in answer:
                continue
            hour = None
            m_time = re.search(r"(오전|오후)\s*(\d{1,2}):([0-5]\d)", raw[:30])
            if m_time:
                hh = int(m_time.group(2))
                if hh == 12:
                    hh = 0
                if m_time.group(1) == "오후":
                    hh += 12
                hour = f"{hh:02d}:{m_time.group(3)}"
            date_str = date.isoformat()
            key = "|".join([remote_slug, date_str, question, answer])
            uid = sha256(key.encode()).hexdigest()[:16]
            records.append({
                "id": "qd-" + uid,
                "app": slug, "app_name": label,
                "question_hint": question[:53] + ("…" if len(question) > 53 else ""),
                "answer": answer, "date": date_str, "time": hour,
                "source": "QUIZDAY 공개 자료", "source_url": url,
                "source_status": "원본 앱 진행 여부 미확인",
                "confidence_label": "외부 참고 정보 · 미검증",
            })
            per_day[date] = per_day.get(date, 0) + 1
    return records

def get_robots():
    r = requests.get(f"https://{HOST}/robots.txt", timeout=TIMEOUT, headers={"User-Agent":AGENT},allow_redirects=False)
    if r.status_code != 200:
        raise RuntimeError(f"robots.txt 상태 {r.status_code}")
    p = RobotFileParser()
    p.parse(r.text.splitlines())
    return p

def fetch_month(url):
    res = requests.get(url, timeout=TIMEOUT, headers={"User-Agent":AGENT, "Accept":"text/html"},
                       stream=True, allow_redirects=False)
    if res.status_code != 200:
        raise RuntimeError(f"HTTP {res.status_code}")
    content = bytearray()
    for chunk in res.iter_content(32768):
        content.extend(chunk)
        if len(content) > MAX_BYTES:
            raise RuntimeError("응답 크기 제한 초과")
    return content.decode("utf-8", errors="replace")

def main():
    now = datetime.now(KST)
    today = now.date().isoformat()
    existing = json.loads(OUTPUT.read_text(encoding="utf-8"))
    try:
        robots = get_robots()
    except (requests.RequestException, RuntimeError) as exc:
        print(f"robots 상태 확인 실패: {exc}")
        return
    incoming = []
    success = 0
    errors = 0
    for remote, title, local in APPS:
        url = f"{BASE}/{remote}/monthly/"
        if not robots.can_fetch(AGENT, url):
            print(f"SKIP disallowed: {remote}")
            continue
        try:
            items = parse_monthly(fetch_month(url), remote, title, local, url, today)
            success += 1
            incoming.extend(items)
            print(f"{title}: {len(items)}건")
        except (requests.RequestException, RuntimeError, OSError) as exc:
            errors += 1
            print(f"SKIP {remote}: {exc}")
        time.sleep(0.3)
    if success == 0 and errors:
        raise SystemExit("Expanded quiz sources unavailable from runner (e.g. HTTP 403). No data published.")
    if incoming:
        merged = merge(existing.get("quizzes", []), incoming, today)
        if merged != existing.get("quizzes", []):
            existing["quizzes"] = merged
            existing["updated_at"] = now.isoformat(timespec="seconds")
            OUTPUT.write_text(json.dumps(existing, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Expanded feeds checked {success}; errors {errors}; collected {len(incoming)}")

if __name__ == "__main__":
    main()
