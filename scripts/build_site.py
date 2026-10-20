#!/usr/bin/env python3
"""Render QuizPick v1 multi-page static HTML from existing source-linked JSON.

Output is generated in site/ during the Pages workflow, and never sent back to
any third-party provider. Do not advertise that an unverified reward is live.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from html import escape
from pathlib import Path
from urllib.parse import urlparse
import json
import os
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
BASE = os.environ.get("QUIZPICK_BASE_PATH", "/quizpick-lite").rstrip("/")
ORIGIN = "https://sean-messiah.github.io"
GA_ID = "G-3Y68828WYZ"
OFFICIAL = {"toss": "https://toss.im/", "kakaobank": "https://www.kakaobank.com/"}
KST = timezone(timedelta(hours=9))
TODAY = datetime.now(KST).date()
SAFE_ID = re.compile(r"^[a-z0-9][a-z0-9_-]{1,90}$")
SAFE_DAY = re.compile(r"^\d{4}-\d{2}-\d{2}$")

APPS = {
    "toss": ("토스", "💙", "금융", "토스 앱 → 혜택에서 해당 퀴즈를 확인하세요.", "행운퀴즈·두근두근 1등찍기"),
    "kakaobank": ("카카오뱅크", "🟡", "금융", "카카오뱅크 앱 → 혜택에서 AI 이모지 또는 OX 퀴즈를 확인하세요.", "AI 이모지·OX 퀴즈"),
    "cashwalk": ("캐시워크", "👟", "캐시", "캐시워크 앱의 돈버는퀴즈 메뉴에서 현재 문제를 확인하세요.", "돈버는퀴즈"),
    "okquiz": ("OK캐쉬백 오퀴즈", "🟠", "캐시", "OK캐쉬백 앱에서 해당 시간대 오퀴즈를 확인하세요.", "오퀴즈"),
    "shinhanpay": ("신한 SOL페이", "💳", "금융", "신한 SOL페이 앱에서 퀴즈팡팡 회차를 확인하세요.", "퀴즈팡팡"),
    "shinhanbank": ("신한 SOL뱅크", "🏦", "금융", "신한 SOL 앱에서 진행 중인 퀴즈를 확인하세요.", "쏠퀴즈"),
    "kbpay": ("KB Pay", "💰", "금융", "KB Pay 앱에서 오늘의 퀴즈를 확인하세요.", "오늘의 퀴즈"),
    "kbstar": ("KB스타뱅킹", "⭐", "금융", "KB스타뱅킹 앱에서 스타퀴즈를 확인하세요.", "스타퀴즈"),
    "cashdoc": ("캐시닥", "🩺", "캐시", "캐시닥 앱에서 용돈퀴즈를 확인하세요.", "용돈퀴즈"),
}

# Original third-party service icons from Toss/KakaoBank branding and developer-published Google Play listings.
# Unmodified source images are presented only as app identifiers, with text/emoji fallbacks.
APP_ICONS = {
    "toss": "https://static.toss.im/icons/png/4x/icon-toss-logo.png",
    "kakaobank": "https://m.kakaobank.com/view/images/sub/symbol-logo.svg",
    "cashwalk": "https://play-lh.googleusercontent.com/AtjN8ZCMqB0OZF2jjKetQscmLGDVVUat_rbQgJJ2Y_sJMp_haQ_RMFVllMit6J2I2f5s7pqWIOirPw69mRjh=w240-h480-rw",
    "okquiz": "https://play-lh.googleusercontent.com/qxw_pDtrlO7BDgJJdPl802eog8dfws1kXrzLXmOGr8kE2AQwiUT88KGwwJOkZUqWDhyYolauN06iGXHVHelGbA=w240-h480-rw",
    "shinhanpay": "https://play-lh.googleusercontent.com/Y2-sVm4TNp5QG__Ac8Ysug7Il9sfBM61L0sJ7zb4vuu98793AG21gaekossyHcOzOrwjHCZ-bXarM4eCzv8nBg=w240-h480-rw",
    "shinhanbank": "https://play-lh.googleusercontent.com/VoHoGvh399BRPls8rz-UpqshdPrZd04kEUTaTwy8bwP2iWBGUPElL0gf9EWDDOSVj7E_gUk3AlQDoFUpqXBwspY=w240-h480-rw",
    "kbpay": "https://play-lh.googleusercontent.com/mHMuGEBy_hFqLdL3BG-Jas0hMX41b0KOaaxHvPLCrhKBcbkhAwX-4d4P_QFjkuie9XPheHq2MAgJ38zJnNvbhg=w240-h480-rw",
    "kbstar": "https://play-lh.googleusercontent.com/OmJa1eJ_ONHHa9SRuhiI2Ouzy7Cb_rhoGF-JQC1pnWxOcMtnNGOs7XrwPoldEJ0ar5eztMqBPn79H7AQDeyk=w240-h480-rw",
    "cashdoc": "https://play-lh.googleusercontent.com/dT5y90tc7EepE9OG7QHi7LZ1lS5iRSDbK_idlmmxyLQZNJ1w4HB0bfyMoLT_1X479Wsu3r2Z1FX5a0QRXB36U1I=w240-h480-rw",
}

def app_icon(slug):
    name, emoji = APPS[slug][0], APPS[slug][1]
    src = APP_ICONS.get(slug)
    if not src:
        return '<span class="appicon" aria-hidden="true">'+e(emoji)+'</span>'
    loading = "eager"  # load compact app symbols immediately so they do not look like emoji placeholders
    return ('<span class="appicon has-logo" aria-hidden="true"><span class="appicon-fallback">'+e(emoji)+'</span>'
            '<img class="app-brand-logo" alt="" src="'+e(src)+'" width="64" height="64" loading="'+loading+'" decoding="async"></span>')

def brand_strip(slug):
    return '<div class="brand-strip">'+app_icon(slug)+'<span><small>QUIZPICK · 앱별 퀴즈</small><strong>'+e(APPS[slug][0])+'</strong></span></div>'

def e(value):
    return escape(str(value or ""), quote=True)

def local(*parts):
    if not parts:
        return BASE + "/"
    return BASE + "/" + "/".join(str(x).strip("/") for x in parts if x != "") + "/"

def static_url(*parts):
    """URLs to real files must not end with a directory slash."""
    if not parts:
        raise ValueError("파일 경로가 필요합니다")
    return BASE + "/" + "/".join(str(x).strip("/") for x in parts)

def absolute(path):
    return ORIGIN + path

def link(label, href, cls="", attrs=""):
    return '<a class="%s" href="%s" %s>%s</a>' % (e(cls), e(href), attrs, e(label))

def page(title, description, body, path, *, noindex=False):
    canonical = absolute(path)
    robots = '<meta name="robots" content="noindex,follow">' if noindex else ""
    return '''<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#fff1f7"><title>%s | 퀴즈픽</title>
<meta name="description" content="%s"><link rel="canonical" href="%s">
<meta property="og:type" content="website"><meta property="og:title" content="%s | 퀴즈픽"><meta property="og:description" content="%s">
<meta property="og:url" content="%s">%s
<script async src="https://www.googletagmanager.com/gtag/js?id=%s"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments)}
gtag('js',new Date());gtag('config','%s')</script>
<link rel="stylesheet" href="%s"><script defer src="%s"></script></head>
<body><a class="skip" href="#content">본문으로 이동</a>
<header class="header"><div class="topbar"><a class="logo" href="%s"><span class="logomark">♥</span><span><span class="wordmark">QUIZ<em>PICK</em></span><small class="brand-ko">퀴즈픽</small></span></a>
<nav class="nav" aria-label="주요 메뉴"><a href="%s">홈</a><a href="%s">전체 퀴즈</a><a href="%s">챌린지</a><a href="%s">이용 안내</a></nav></div></header>
<main id="content" class="main">%s</main>
<footer class="footer"><div>퀴즈픽은 공식 앱과 무관한 독립 정보 서비스입니다. 원본 앱에서 정답과 리워드 지급 조건을 최종 확인하세요.</div><div>각 서비스명 및 심볼의 권리는 해당 운영사에 있으며, 퀴즈 정보를 구분하기 위한 목적으로만 표시합니다. 공식 제휴·후원을 의미하지 않습니다.</div>
<div class="footnav"><a href="%s">서비스 소개</a><a href="%s">개인정보 처리 안내</a><a href="%s">정답 검증 기준</a><a href="%s">문의·정정</a></div>
<div>© QuizPick Lite · 보상 지급 주체가 아닙니다</div></footer>
<nav class="mobile-nav" aria-label="모바일 하단 메뉴"><a href="%s"><span class="tab-icon" aria-hidden="true">⌂</span>홈</a><a href="%s"><span class="tab-icon" aria-hidden="true">☷</span>전체퀴즈</a><a href="%s"><span class="tab-icon" aria-hidden="true">◎</span>챌린지</a><a href="%s"><span class="tab-icon" aria-hidden="true">♡</span>즐겨찾기</a><a href="%s"><span class="tab-icon" aria-hidden="true">☰</span>메뉴</a></nav>
<div class="toast" id="toast" role="status" aria-live="polite"></div></body></html>
''' % (e(title),e(description),e(canonical),e(title),e(description),
       e(canonical),robots,e(GA_ID),e(GA_ID),e(static_url("assets","style.css")),
       e(static_url("assets","app.js")),e(local()),e(local()),e(local("apps")),
       e(local("challenge")),e(local("about")),body,e(local("about")),e(local("privacy")),e(local("editorial-policy")),e(local("contact")),
       e(local()),e(local("apps")),e(local("challenge")),e(local("saved")),e(local("menu")))

def write(path, html):
    dest=SITE/path.strip("/")/"index.html" if path else SITE/"index.html"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(html,encoding="utf-8")
    return dest

def split_toss_prizes(answer):
    """Separate published first/second choices without inventing any response."""
    raw = str(answer or "").strip()
    matches = list(re.finditer(r"(?<!\S)(일등|1등|이등|2등)\s*[:：]?\s*", raw))
    if len(matches) != 2 or matches[0].start() != 0:
        return []
    first = matches[0].group(1)
    second = matches[1].group(1)
    if first not in ("일등", "1등") or second not in ("이등", "2등"):
        return []
    a = raw[matches[0].end():matches[1].start()].strip()
    b = raw[matches[1].end():].strip()
    if not a or not b:
        return []
    return [("1등", a), ("2등", b)]


def curate_rows(rows):
    """Remove missing-question duplicates, retaining distinct questions even if answers match."""
    groups = defaultdict(list)
    for row in rows:
        key = (row.get("app"), row.get("date"), row.get("source_url"), str(row.get("answer", "")).strip().casefold())
        groups[key].append(row)
    hidden = set()
    for batch in groups.values():
        complete = [r for r in batch if summary(r) != "문제 요약 확인 필요"]
        if complete:
            hidden.update(r["id"] for r in batch if summary(r) == "문제 요약 확인 필요")
    seen = set()
    result = []
    for row in rows:
        if row.get("id") in hidden:
            continue
        k = (row.get("app"),row.get("date"),row.get("source_url"),
             str(row.get("question_hint", "")).strip(),str(row.get("answer", "")).strip())
        if k in seen:
            continue
        seen.add(k)
        result.append(row)
    return result


def verified_rows():
    payload=json.loads((SITE/"data.json").read_text(encoding="utf-8"))
    earliest=TODAY-timedelta(days=6)
    rows=[]
    for raw in payload.get("quizzes",[]):
        slug=raw.get("app")
        day=raw.get("date","")
        rid=raw.get("id","")
        if slug not in APPS or not SAFE_DAY.fullmatch(day) or not SAFE_ID.fullmatch(rid):
            continue
        try:
            d=datetime.strptime(day,"%Y-%m-%d").date()
        except ValueError:
            continue
        if not earliest<=d<=TODAY or not raw.get("answer"):
            continue
        source=raw.get("source_url","")
        p=urlparse(source)
        if p.scheme!="https" or not p.hostname:
            continue
        rows.append(raw)
    return curate_rows(rows)

def app_path(slug):
    return local(slug) if slug in ("toss","kakaobank") else local("apps",slug)

def quiz_path(row):
    return local("quiz", row["app"],row["date"],row["id"])

def day_path(slug, date):
    return local("quiz",slug,date)

def summary(row):
    txt=row.get("question_hint") or "문제 제목을 확인해 주세요."
    return "문제 요약 확인 필요" if txt=="문제 문구 확인 불가" else txt

def label(row):
    if row["app"]=="kakaobank":
        if "OX" in summary(row).upper():
            return "OX 퀴즈"
        return "AI 이모지 퀴즈"
    if row["app"]=="toss":
        if "두근" in summary(row) or "1등" in summary(row):
            return "두근두근 1등찍기"
        return "행운퀴즈"
    return APPS[row["app"]][4]

def state(row):
    return "오늘 게시된 참고 정답 · 현재 참여 여부 미확인" if row["date"]==TODAY.isoformat() else "지난 회차 참고 정답 · 현재 보상 지급 여부 미확인"

def item_card(row, kind="tile"):
    href=quiz_path(row)
    body='<span class="eyebrow">%s · %s%s</span>'%(e(label(row)),e(row["date"]),(" "+e(row.get("time")) if row.get("time") else ""))
    body+='<strong>%s</strong><small>정답은 상세 페이지에서 확인 · 진행 여부 미확인</small>'%e(summary(row))
    return '<a class="quizcard" href="%s" data-event="quiz_select" data-app="%s">%s<span class="arr">정답 보기 →</span></a>'%(e(href),e(row["app"]),body)

def app_summary(slug, rows):
    name,icon,_,_,sub=APPS[slug]
    current=sum(r["date"]==TODAY.isoformat() for r in rows)
    report=("오늘 공개 참고 정답 %d건 · 현재 참여 여부 미확인"%current) if current else "최근 7일 참고 기록 · 오늘 출제 여부 미확인"
    cta='<span class="card-cta">회차별 정답 확인하기 →</span>' if slug in ("toss","kakaobank") else ""
    return '''<a class="appcard" data-app="%s" href="%s" data-event="home_app_click">
    %s<span><strong>%s</strong><small>%s</small>
    <span class="appstat">%s</span></span><span class="chevron" aria-hidden="true">›</span>%s</a>'''%(
        e(slug),e(app_path(slug)),app_icon(slug),e(name),e(sub),e(report),cta)

def breadcrumb(*nodes):
    links=[]
    for title,path in nodes:
        links.append(link(title,path))
    return '<nav class="breadcrumbs" aria-label="현재 위치">'+ ' <span aria-hidden="true">›</span> '.join(links)+'</nav>'

def heading(kicker,title,lead, level="h1"):
    tag="h2" if level=="h2" else "h1"
    return '<div class="section-head"><div class="eyebrow">%s</div><%s>%s</%s><p>%s</p></div>'%(e(kicker),tag,e(title),tag,e(lead))

def quiz_group(slug, dated_rows):
    dates=sorted(dated_rows,reverse=True)
    html=''
    for date in dates:
        rows=dated_rows[date]
        if len(rows)==1:
            dest=quiz_path(rows[0])
        else:
            dest=day_path(slug,date)
        html+='<a class="daycard" href="%s" data-event="app_quiz_click" data-app="%s"><span><strong>%s</strong><small>정답 기록 %d건 · %s</small></span><span class="arr">회차 확인 →</span></a>'%(e(dest),e(slug),e(date),len(rows),"오늘 공개 자료" if date==TODAY.isoformat() else "지난 회차")
    return html

def main():
    rows=verified_rows()
    # Small manifest lets saved bookmarks avoid vanished detail routes after a refresh.
    (SITE/"active-quizzes.json").write_text(
        json.dumps({"date":TODAY.isoformat(),"paths":[quiz_path(q) for q in rows]},ensure_ascii=False),
        encoding="utf-8"
    )
    byapp=defaultdict(list)
    byday=defaultdict(list)
    for row in rows:
        byapp[row["app"]].append(row)
        byday[(row["app"],row["date"])].append(row)
    for value in byapp.values():
        value.sort(key=lambda x:(x["date"],x.get("time") or "",x["id"]),reverse=True)
    p0=["toss","kakaobank"]
    remaining=[x for x in ("cashwalk","okquiz","shinhanpay","shinhanbank","cashdoc","kbpay","kbstar") if byapp[x]]
    apporder=p0+remaining

    hero='''<section class="hero"><div class="hero-copy"><span class="eyebrow light">💕 오늘도 퀴즈픽!</span>
    <h1>오늘의 앱테크 <strong>퀴즈</strong><br>정답을 한곳에서!</h1>
    <p>토스·카카오뱅크 먼저! 앱별 문제와 회차를 확인하고 정답을 복사해 보세요.</p>
    <div class="hero-date">📅 한국시간 %s 기준 · 최근 7일 공개 참고 정답 %d건</div></div>
    <div class="hero-art" aria-hidden="true"><span class="hero-bunny">🐰</span><span class="hero-coin">🪙</span><span class="hero-gift">🎁</span></div>
    </section>'''%(e(TODAY.isoformat()),len(rows))
    homes=heading("⭐ 우선 확인","토스 · 카카오뱅크","먼저 찾는 두 앱의 정답은 회차별 상세 페이지에서 확인하세요.",level="h2")
    homes+='<div class="featured">'+''.join(app_summary(x,byapp[x]) for x in p0)+'</div>'
    others=heading("🎁 앱테크 더보기","다른 퀴즈도 확인해요","최근 7일 공개 정답 참고 자료가 있는 앱만 표시합니다.",level="h2")
    others+='<div class="apps-grid">'+''.join(app_summary(x,byapp[x]) for x in remaining)+'</div>'
    others+='<p class="inline-action">'+link("전체 앱 보기 →",local("apps"))+'</p>'
    challengepromo='<section class="challenge-promo" aria-label="매일 앱테크 챌린지"><div><span class="eyebrow">🎯 100일 저축 챌린지</span><h2>오늘 50원, 100원 기록하기</h2><p>100일 체크로 나만의 목표를 채워 보세요. 금 0.1돈 모으기도 도전할 수 있어요.</p></div>'+link("챌린지 시작 →",local("challenge"),"primary-action")+'</section>'
    sections='<section class="section">'+homes+'</section>'+challengepromo+'<section class="section">'+others+'</section>'
    guide='''<section class="info"><h2>퀴즈픽 이용 방법</h2><p>앱 이름을 선택한 뒤 날짜와 회차를 확인하세요. 정답 상세에서 복사한 내용은 반드시 원본 앱에서 다시 확인해 주세요. 퀴즈는 마감·변경될 수 있으며 퀴즈픽이 포인트를 지급하지 않습니다.</p></section>'''
    homebody=hero+sections+guide
    write("",page("오늘의 토스·카카오뱅크 앱테크 퀴즈", "토스 행운퀴즈와 카카오뱅크 AI 이모지 퀴즈부터 날짜와 회차별 공개 정답을 확인하세요. 리워드는 원본 앱에서 제공합니다.",homebody,local()))

    allbody=breadcrumb(("홈",local()))+heading("QUIZ DIRECTORY","앱테크 퀴즈 전체 목록","최근 7일 정답 출처가 확인된 앱을 먼저 표시합니다. 과거 이벤트나 미확인 서비스는 현재 참여 가능하다고 표시하지 않습니다.")
    allbody+='<label class="finder">앱 이름 검색 <input type="search" id="app-search" placeholder="토스, 카카오뱅크, 캐시워크..." autocomplete="off"></label>'
    allbody+='<p class="eyebrow" id="search-count" aria-live="polite"></p><div class="apps-grid app-list">'+''.join(app_summary(x,byapp[x]) for x in apporder)+'</div>'
    catalog_data=json.loads((SITE/"catalog.json").read_text(encoding="utf-8"))
    active=set(apporder)
    candidates=[]
    for entry in catalog_data.get("apps",[]):
        name, appid = entry.get("name",""), entry.get("id","")
        if not name or appid in active or active.intersection(entry.get("aliases",[])):
            continue
        if entry.get("feed") == "ended" or appid in {"climate"}:
            continue  # officially ended programs must not be suggested as active candidates
        source=entry.get("source_url","")
        parsed=urlparse(source)
        if parsed.scheme != "https" or not parsed.hostname:
            continue
        note="과거 이벤트 · 현재 운영 미확인" if entry.get("feed")=="historical_unverified" else "현재 정답·리워드 지급 미확인"
        candidates.append('<a class="directory-card" href="'+e(source)+'" target="_blank" rel="noopener noreferrer" data-app="'+e(appid)+'"><strong>'+e(name)+'</strong><small>'+e(note)+'</small><span>공개 출처 확인 ↗</span></a>')
    if candidates:
        allbody+='<details id="candidate-details" class="candidate-details"><summary>운영 확인 대기 · 기타 후보 '+str(len(candidates))+'개</summary><p class="notice">아래 항목은 현재 리워드 지급을 확인하지 못했습니다. 정답이 있다고 표시하지 않으며 출처 링크만 제공합니다.</p><div class="apps-grid app-list">'+''.join(candidates)+'</div></details>'
    allbody+='<div class="empty-panel" id="search-empty" hidden><strong>검색 결과가 없어요 🔎</strong><p>다른 앱 이름으로 검색하거나 검색어를 지워 주세요.</p></div>'
    allbody+='<div class="info"><h2>왜 모든 앱을 표시하지 않나요?</h2><p>종료된 이벤트와 운영 확인이 어려운 퀴즈를 현재 참여 가능한 것처럼 안내하지 않기 위해서입니다. 정답이 있는 앱도 보상 지급 여부는 앱에서 다시 확인해야 합니다.</p></div>'
    write("apps",page("앱테크 퀴즈 전체 목록","토스, 카카오뱅크, 캐시워크 등 공개 정답 자료가 확인된 앱 모음.",allbody,local("apps")))

    for slug in apporder:
        name,icon,_,instructions,subtitle=APPS[slug]
        arr=byapp[slug]
        dated=defaultdict(list)
        for q in arr:
            dated[q["date"]].append(q)
        appbody=breadcrumb(("홈",local()),("전체 앱",local("apps")))
        appbody+=brand_strip(slug)+heading(subtitle,name+" 퀴즈 정답","오늘의 회차와 지난 7일 공개 기록을 날짜별로 확인하세요.")
        if slug in p0:
            expected=("행운퀴즈","두근두근 1등찍기") if slug=="toss" else ("AI 이모지 퀴즈","OX 퀴즈")
            today_by_type={t:sum(q["date"]==TODAY.isoformat() and label(q)==t for q in arr) for t in expected}
            appbody+='<section class="info"><h2>오늘 유형별 공개 정답</h2><div class="pills">'+''.join(
                '<span>'+e(t)+' · '+(str(today_by_type[t])+'건 게시' if today_by_type[t] else '오늘 확인된 정답 없음')+'</span>'
                for t in expected
            )+'</div><p>오늘 정답이 등록되지 않았다고 해서 원본 앱에서 퀴즈가 진행되지 않는다는 뜻은 아닙니다.</p></section>'
        appbody+='<section class="info"><h2>어디서 참여하나요?</h2><p>'+e(instructions)+'</p><p>공개 정답이 등록돼도 현재 회차가 열려 있거나 리워드가 남았다는 뜻은 아닙니다.</p>'
        if slug in OFFICIAL:
            appbody+='<p>'+link("공식 홈페이지 열기 ↗",OFFICIAL[slug],"source-link",
                               'target="_blank" rel="noopener noreferrer" data-event="official_site_click" data-app="'+e(slug)+'"')+'</p>'
        appbody+='</section>'
        appbody+='<section class="section">'+heading("날짜별 확인","퀴즈 날짜 선택","정답이 등록된 날짜만 표시합니다.")
        appbody+=('<div class="days">'+quiz_group(slug,dated)+'</div>' if dated else '<div class="empty-panel"><strong>최근 등록된 정답이 없어요</strong><p>현재 출제·리워드 여부는 앱에서 직접 확인해 주세요.</p></div>')+'</section>'
        appbody+='<p class="inline-action">'+link("다른 앱테크 퀴즈 둘러보기 →",local("apps"))+'</p>'
        write(app_path(slug).removeprefix(BASE+"/").strip("/"),
              page(name+" 오늘의 퀴즈 정답 · 날짜별 목록",name+"의 최근 회차, 공개 정답 기록 및 참여 방법.",appbody,app_path(slug)))

    for (slug,date),rs in byday.items():
        name=APPS[slug][0]
        rs.sort(key=lambda x: (x.get("time") or "",x["id"]),reverse=True)
        body=breadcrumb(("홈",local()),(name,app_path(slug)))
        body+=brand_strip(slug)+heading("DATE · "+date,name+" "+date+" 퀴즈 회차","날짜와 문제 요약을 비교하고 해당 정답 페이지를 선택하세요.")
        body+='<p class="notice">'+("오늘 게시된 외부 참고 정보입니다." if date==TODAY.isoformat() else "지난 회차의 외부 참고 정보입니다.")+' 현재 참여 가능 여부나 적립 보상을 보장하지 않습니다.</p>'
        body+='<div class="quizlist">'+''.join(item_card(x) for x in rs)+'</div>'
        body+='<p class="inline-action">'+link("← "+name+" 날짜 목록",app_path(slug))+'</p>'
        write(day_path(slug,date).removeprefix(BASE+"/").strip("/"),
              page(name+" "+date+" 문제별 정답 목록",name+"의 "+date+" 공개 문제와 회차를 선택하세요. 정답은 각 상세에서 표시됩니다.",body,day_path(slug,date),
                   noindex=len(rs)<=1))
        for row in rs:
            qpath=quiz_path(row)
            qtitle=label(row)+" "+row["date"]+" 정답"
            body=breadcrumb(("홈",local()),(name,app_path(slug)),(date,day_path(slug,date)))
            body+=brand_strip(slug)+heading(label(row),name+" "+row["date"]+" 정답 확인","회차: "+(row.get("time") or "출제시각 미확인")+" · "+state(row))
            body+='<div class="detail-actions"><span class="pills"><span>💗 외부 공개 참고 자료</span></span><button class="savebtn" type="button" aria-pressed="false" data-save-quiz data-app="'+e(slug)+'" data-url="'+e(qpath)+'" data-title="'+e(name+" "+row["date"]+" "+label(row))+'" data-date="'+e(row["date"])+'" data-answer="'+e(row["answer"])+'" data-question="'+e(summary(row))+'">♡ 즐겨찾기에 저장</button></div>'
            body+='<section class="question-detail"><h2>문제 정보</h2><p>'+e(summary(row))+'</p></section>'
            prize_options = split_toss_prizes(row["answer"]) if slug=="toss" and label(row)=="두근두근 1등찍기" else []
            body+='<section class="answer-detail"><div class="eyebrow">✅ 외부 공개 자료에 게시된 참고 정답</div>'
            if prize_options:
                for rank, value in prize_options:
                    body+='<div class="answer-option"><strong>'+e(rank)+' 상품</strong><div class="answer-value">'+e(value)+'</div><button class="copybtn" type="button" data-copy-answer data-copy-text="'+e(value)+'" data-app="'+e(slug)+'">📋 '+e(rank)+' 항목 복사</button></div>'
            else:
                body+='<div class="answer-value" id="answer-value">'+e(row["answer"])+'</div><button class="copybtn" type="button" data-copy-answer data-app="'+e(slug)+'">📋 정답 복사하기</button>'
            body+='<p>원본 앱의 문제·회차가 같은지 꼭 확인하세요. 보상 지급은 퀴즈픽이 아닌 해당 앱에서 이루어집니다.</p></section>'
            source=row.get("source_url","")
            body+='<div class="steps" aria-label="퀴즈 참여 절차"><div class="step"><strong>① 문제 확인</strong>앱과 회차를 확인해요</div><div class="step"><strong>② 정답 복사</strong>정답을 복사해요</div><div class="step"><strong>③ 공식 앱 참여</strong>해당 앱에서 직접 참여해요</div></div>'
            body+='<section class="info"><h2>참여 방법과 확인 사항</h2><p>'+e(APPS[slug][3])+'</p>'
            body+='<p>정답 출처: '+e(row.get("source","외부 공개 자료"))+' · '+e(row.get("confidence_label","외부 미검증"))+'</p>'
            body+='<p>현재 회차 참여·지급 여부: 미확인. 보상은 원본 앱에서 지급되며 시간·대상·잔여 수량에 따라 달라질 수 있습니다.</p>'
            if slug in OFFICIAL:
                body+='<p>'+link("해당 앱 공식 홈페이지 ↗",OFFICIAL[slug],"source-link",
                                 'target="_blank" rel="noopener noreferrer" data-event="official_site_click" data-app="'+e(slug)+'"')+'</p>'
            body+='<p>'+link("게시된 원문 확인 ↗",source,"source-link", 'target="_blank" rel="noopener noreferrer" data-event="source_open" data-app="'+e(slug)+'"')+'</p></section>'
            rec=[x for x in rs if x["id"]!=row["id"]][:3]
            if rec:
                body+='<section class="section">'+heading("RELATED","같은 날짜 다른 정답","다른 문제나 회차를 확인할 수 있습니다.")+'<div class="quizlist">'+''.join(item_card(x) for x in rec)+'</div></section>'
            body+='<p class="inline-action">'+link("← "+name+" 전체 회차",app_path(slug))+'</p>'
            write(qpath.removeprefix(BASE+"/").strip("/"),
                  page(qtitle+" · "+summary(row),name+" "+date+" "+label(row)+" 답을 확인하고 복사하세요. 원본 앱 회차와 보상을 확인하세요.",body,qpath,noindex=True))

    challengebody=breadcrumb(("홈",local()))+heading("QUIZPICK · 100 DAYS","매일 50원·100원 모으기 챌린지",
        "내가 앱테크로 모은 금액을 100일간 직접 기록하고, 작은 목표가 얼마나 쌓이는지 확인하세요.")
    challengebody+='''<div class="challenge-stats"><div><strong>50원 × 100일</strong><span>5,000원</span></div>
      <div><strong>100원 × 100일</strong><span>10,000원</span></div>
      <div><strong>금 0.1돈</strong><span>0.375g</span></div></div>
      <p class="notice">⚠️ 이 챌린지는 <strong>직접 기록하는 목표 관리 도구</strong>입니다. 퀴즈픽이 포인트·현금·금을 지급하거나 실제 앱 적립을 인증하지 않습니다.</p>
      <div id="challenge-app" class="challenge-app"><noscript>챌린지 기록 기능은 자바스크립트가 켜진 브라우저에서 이용할 수 있습니다.</noscript></div>'''
    challengebody+='<section class="info challenge-guide"><h2>100일 챌린지는 어떻게 진행하나요?</h2><p>닉네임을 입력해 이 기기에서 시작하세요. 하루 50원 또는 100원을 목표로 정하고 실제로 모은 금액을 매일 직접 기록하면 체크 수와 누적 금액이 계산됩니다. 하루에 여러 번 눌러도 해당 날짜의 기록이 중복되지 않고 수정할 수 있습니다.</p><p>금 0.1돈은 무게로 0.375g입니다. 실제 금 가격, 구매 수수료 등은 달라질 수 있으므로 구매에 필요한 예산을 직접 정하고 그 금액을 향해 모은 돈을 기록해 주세요.</p><p>현재는 로그인·기기간 동기화가 없는 기기 저장형 체험 기능입니다. 브라우저 데이터 삭제 시 기록이 사라질 수 있으니 기록 관리에서 파일로 백업하세요. 실제 계정 가입 기능은 별도 서버·인증을 구성한 뒤 적용할 계획입니다.</p></section>'
    challengebody+='<section class="challenge-partners"><h2>함께 준비 중인 서비스</h2><div class="challenge-grid"><div class="challenge-partner"><strong>🎮 가벼운 미니게임</strong><p>별도로 배포하고, 실제 서비스 주소가 생기면 상호 배너로 연결합니다.</p><span>준비 중</span></div><div class="challenge-partner"><strong>🛒 장보기 서비스</strong><p>기존 장보기 프로젝트가 공개되면 관련 배너와 서비스 이동을 연결합니다.</p><span>연동 준비 중</span></div></div></section>'
    challengebody+='<script defer src="'+e(static_url("assets","challenge.js"))+'"></script>'
    write("challenge",page("100일 앱테크 50원·100원 챌린지 · 금 0.1돈 목표",
        "매일 50원·100원을 기록하고 100일 누적 금액을 계산하는 앱테크 도전. 금 0.1돈(0.375g) 예산 목표도 직접 설정하세요.",
        challengebody,local("challenge")))

    info_pages=[
      ("about","퀴즈픽 소개","퀴즈픽은 앱테크 퀴즈의 공개 정답 참고 자료와 참여 방법을 모아 제공하는 독립 서비스입니다. 토스·카카오뱅크를 먼저 보여주며, 각 운영사와 제휴하거나 이들로부터 리워드를 지급받는 서비스가 아닙니다."),
      ("privacy","개인정보 및 방문 통계 안내","이 웹사이트는 회원가입, 결제 또는 개인별 정답 제출 기록을 요구하지 않습니다. 방문 통계 목적으로 Google Analytics 4를 사용하여 페이지 방문과 버튼 이용 집계가 전송될 수 있습니다. 웹 브라우저 설정이나 광고·추적 차단 기능으로 분석을 제한할 수 있습니다. 개인정보 및 방문 분석 문의는 공개 GitHub 저장소의 이슈 기능을 이용할 수 있습니다."),
      ("editorial-policy","정답 검증·정정 기준","퀴즈픽은 원본 앱이 아닌 공개 자료를 참고합니다. 게시된 답은 변경될 수 있으며 원본 앱에서 최종 확인해야 합니다. 회차 마감·보상 지급 가능 여부를 앱에서 실시간 확인하지 않은 경우 '미확인'으로 표시합니다. 잘못된 답이나 출처 정정은 GitHub 저장소의 공개 이슈로 제보해 주세요."),
      ("contact","문의 및 정정 요청","잘못된 정답이나 출처, 서비스 이용 문의는 아래 GitHub 프로젝트의 이슈 기능을 통해 접수할 수 있습니다. 문제 발생 날짜·앱 이름·페이지 주소를 함께 남겨주시면 확인에 도움이 됩니다."),
    ]
    for path,title,description in info_pages:
        text=breadcrumb(("홈",local()))+heading("QUIZPICK",title,description)
        text+='<p class="inline-action">'+link("GitHub 프로젝트와 정정 요청 ↗","https://github.com/Sean-messiah/quizpick-lite/issues","source-link",'target="_blank" rel="noopener noreferrer"')+'</p>'
        write(path,page(title,description,text,local(path)))

    savedbody=breadcrumb(("홈",local()))+heading("MY QUIZ","즐겨찾기한 퀴즈","나중에 다시 볼 정답 상세 페이지를 이 브라우저에만 보관합니다.")
    savedbody+='<div class="saved-list" id="saved-list" aria-live="polite"></div><div class="empty-panel" id="saved-empty"><strong>저장한 퀴즈가 없어요 ♡</strong><p>정답 상세 화면에서 하트 버튼을 눌러 저장해 보세요.</p><p>'+link("퀴즈 둘러보기 →",local("apps"),"source-link")+'</p></div>'
    write("saved",page("내 즐겨찾기","브라우저에 저장된 퀴즈픽 정답 목록",savedbody,local("saved"),noindex=True))
    menubody=breadcrumb(("홈",local()))+heading("QUIZPICK","전체 메뉴","퀴즈픽의 앱테크 정답과 이용 정보를 빠르게 찾으세요.")
    menubody+='<div class="apps-grid">'+''.join('<a class="daycard" href="'+e(path)+'"><strong>'+e(title)+'</strong><span class="arr">열기 →</span></a>' for title,path in (("오늘의 퀴즈",local()),("전체 앱테크 퀴즈",local("apps")),("즐겨찾기",local("saved")),("100일 챌린지",local("challenge")),("서비스 소개",local("about")),("정답 검증 기준",local("editorial-policy")),("문의·정정",local("contact")),("개인정보 안내",local("privacy"))))+'</div>'
    write("menu",page("전체 메뉴","퀴즈픽 앱테크 서비스 메뉴",menubody,local("menu")))
    notfound=heading("404 · NOT FOUND","페이지를 찾을 수 없어요","주소가 잘못됐거나 오래된 퀴즈 기록일 수 있어요. 다른 퀴즈를 찾아보세요.")
    notfound+='<div class="empty-panel"><strong>길을 잃었나요? 🐰</strong><p>'+link("홈으로 돌아가기 →",local(),"primary-action")+'</p></div>'
    (SITE/"404.html").write_text(page("페이지를 찾을 수 없습니다","찾을 수 없는 퀴즈픽 페이지입니다.",notfound,local(),noindex=True),encoding="utf-8")
    urls=[local(),local("apps"),local("menu"),local("challenge")]+[app_path(x) for x in apporder]
    for path,_,_ in info_pages:
        urls.append(local(path))
    # Detailed answer pages are intentionally noindex (brief externally sourced facts).
    for slug,date in byday:
        if len(byday[(slug,date)])>1:
            urls.append(day_path(slug,date))
    root=ET.Element("urlset",xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
    for path in dict.fromkeys(urls):
        u=ET.SubElement(root,"url")
        ET.SubElement(u,"loc").text=absolute(path)
        ET.SubElement(u,"lastmod").text=TODAY.isoformat()
    ET.ElementTree(root).write(SITE/"sitemap.xml",encoding="utf-8",xml_declaration=True)
    (SITE/"robots.txt").write_text("User-agent: *\nAllow: /\nSitemap: "+absolute(static_url("sitemap.xml"))+"\n",encoding="utf-8")
    print("built v1:",len(rows),"quizzes,",len(apporder),"apps,",len(byday),"date pages")

if __name__=="__main__":
    main()
