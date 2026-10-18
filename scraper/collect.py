#!/usr/bin/env python3
"""QuizPick Lite: low-frequency public-page collection, no access-control bypass."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser
import hashlib
import json
import re

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "site" / "data.json"
SOURCES = ROOT / "scraper" / "sources.json"
KST = timezone(timedelta(hours=9))
AGENT = "QuizPickLiteBot/0.1 (source-linked public quiz reference)"
TIMEOUT = 12

def get_app(text):
    mapping = [
        ("신한카드", "shinhanpay", "신한 SOL페이"),
        ("SOL페이", "shinhanpay", "신한 SOL페이"),
        ("퀴즈팡팡", "shinhanpay", "신한 SOL페이"),
        ("신한", "shinhanbank", "신한 SOL뱅크"),
        ("KB Pay 오늘의 퀴즈", "kbpay", "KB Pay"),
        ("KB스타뱅킹", "kbstar", "KB스타뱅킹"),
        ("스타퀴즈", "kbstar", "KB스타뱅킹"),
        ("캐시워크", "cashwalk", "캐시워크"),
        ("캐시닥", "cashdoc", "캐시닥"),
        ("토스", "toss", "토스"),
        ("오퀴즈", "okquiz", "오퀴즈"),
        ("타임스프레드", "timespread", "타임스프레드"),
        ("KB Pay", "kbpay", "KB Pay"),
    ]
    for word, slug, name in mapping:
        if word in text:
            return slug, name
    return "other", "기타 앱테크"

def parse_quizzes(html, source_url, date):
    soup = BeautifulSoup(html, "html.parser")
    found = []
    for article in soup.select("article"):
        flat = " ".join(article.stripped_strings)
        answer = None
        for item in article.select("p, div"):
            txt = " ".join(item.stripped_strings).strip()
            match = re.fullmatch(r"정답\s*[:：]?\s*(.+?)(?:\s*복사)?", txt)
            if match:
                candidate = match.group(1).strip()
                if candidate and len(candidate) <= 80 and not any(x in candidate for x in ("확인 중", "아직", "출제 전")):
                    answer = candidate
                    break
        if answer is None:
            continue
        heading = article.find("h3")
        question = heading.get_text(" ", strip=True) if heading else "문제 문구 확인 불가"
        slug, name = get_app(flat[:220])
        clock = re.search(r"\b([012]\d:[0-5]\d)\b", flat)
        hour = clock.group(1) if clock else None
        identity = "|".join((date, slug, hour or "", question))
        uid = hashlib.sha256(identity.encode()).hexdigest()[:16]
        found.append({
            "id": "salbopick-" + uid,
            "app": slug,
            "app_name": name,
            "question_hint": question[:64] + ("…" if len(question) > 64 else ""),
            "answer": answer,
            "date": date,
            "time": hour,
            "source": "살보픽 투데이",
            "source_url": source_url,
            "source_status": "마감 표시" if "마감" in flat else "진행 여부 미확인",
            "confidence_label": "외부 게시 정보 · 미검증",
        })
    return found

def fetch_html(url, host):
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname != host or parsed.port or not parsed.path.startswith("/today/quiz/date/"):
        raise RuntimeError("수집 허용 목록에 없는 주소")
    headers = {"User-Agent": AGENT, "Accept": "text/html"}
    robots = requests.get("https://" + host + "/robots.txt", headers=headers, timeout=TIMEOUT, allow_redirects=False)
    if robots.status_code == 200:
        parser = RobotFileParser()
        parser.parse(robots.text.splitlines())
        if not parser.can_fetch(AGENT, url):
            raise RuntimeError("robots 정책에서 허용되지 않음")
    elif robots.status_code != 404:
        raise RuntimeError("robots 상태 확인 실패: " + str(robots.status_code))
    result = requests.get(url, headers=headers, timeout=TIMEOUT, allow_redirects=False, stream=True)
    if result.status_code != 200:
        raise RuntimeError("원본 HTTP " + str(result.status_code))
    buf = bytearray()
    for chunk in result.iter_content(32768):
        buf.extend(chunk)
        if len(buf) > 800000:
            raise RuntimeError("응답이 너무 큼")
    return bytes(buf).decode("utf-8", errors="replace")

def merge(old, incoming, today):
    start = (datetime.strptime(today, "%Y-%m-%d") - timedelta(days=6)).date()
    items = {}
    for record in old + incoming:
        try:
            d = datetime.strptime(record["date"], "%Y-%m-%d").date()
            if start <= d <= datetime.strptime(today, "%Y-%m-%d").date():
                items[record["id"]] = record
        except (ValueError, TypeError, KeyError):
            continue
    return sorted(items.values(), key=lambda x: (x["date"], x.get("time") or "", x["id"]), reverse=True)[:250]

def main():
    now = datetime.now(KST)
    date = now.date().isoformat()
    previous = json.loads(OUTPUT.read_text(encoding="utf-8"))
    config = json.loads(SOURCES.read_text(encoding="utf-8"))
    collected = []
    for source in config.get("sources", []):
        if not source.get("enabled"):
            continue
        url = source["url_template"].format(date=date)
        try:
            html = fetch_html(url, source["host"])
            new = parse_quizzes(html, url, date)
            print(source["id"] + ": " + str(len(new)) + "건")
            collected.extend(new)
        except (RuntimeError, requests.RequestException, OSError) as exc:
            print("SKIP " + source["id"] + ": " + str(exc))
    if not collected:
        print("성공 데이터 없음: 기존 데이터 보존")
        return
    records = merge(previous.get("quizzes", []), collected, date)
    if records == previous.get("quizzes", []) and previous.get("source_mode") == "public-page":
        print("변경 없음")
        return
    doc = {
        "schema_version": 1,
        "updated_at": now.isoformat(timespec="seconds"),
        "source_mode": "public-page",
        "notice": "외부 공개 페이지 참고 정보입니다. 정답과 진행 여부는 원본 앱에서 확인하세요.",
        "quizzes": records,
    }
    OUTPUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("저장: " + str(len(records)) + "건")

if __name__ == "__main__":
    main()
