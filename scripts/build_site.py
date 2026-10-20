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

def e(value):
    return escape(str(value or ""), quote=True)

def local(*parts):
    if not parts:
        return BASE + "/"
    return BASE + "/" + "/".join(str(x).strip("/") for x in parts if x != "") + "/"

def absolute(path):
    return ORIGIN + path

def link(label, href, cls="", attrs=""):
    return '<a class="%s" href="%s" %s>%s</a>' % (e(cls), e(href), attrs, e(label))

def page(title, description, body, path, *, noindex=False):
    canonical = absolute(path)
    robots = '<meta name="robots" content="noindex,follow">' if noindex else ""
    return '''<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#213764"><title>%s | 퀴즈픽</title>
<meta name="description" content="%s"><link rel="canonical" href="%s">
<meta property="og:type" content="website"><meta property="og:title" content="%s | 퀴즈픽"><meta property="og:description" content="%s">
<meta property="og:url" content="%s">%s
<script async src="https://www.googletagmanager.com/gtag/js?id=%s"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments)}
gtag('js',new Date());gtag('config','%s')</script>
<link rel="stylesheet" href="%s"><script defer src="%s"></script></head>
<body><a class="skip" href="#content">본문으로 이동</a>
<header class="header"><div class="topbar"><a class="logo" href="%s"><span class="logomark">✓</span> 퀴즈픽</a>
<nav class="nav" aria-label="주요 메뉴"><a href="%s">홈</a><a href="%s">전체 앱</a><a href="%s">이용 안내</a></nav></div></header>
<main id="content" class="main">%s</main>
<footer class="footer"><div>퀴즈픽은 공식 앱과 무관한 독립 정보 서비스입니다. 원본 앱에서 정답과 리워드 지급 조건을 최종 확인하세요.</div>
<div class="footnav"><a href="%s">서비스 소개</a><a href="%s">개인정보 처리 안내</a><a href="%s">정답 검증 기준</a></div>
<div>© QuizPick Lite · 보상 지급 주체가 아닙니다</div></footer>
<div class="toast" id="toast" role="status" aria-live="polite"></div></body></html>
''' % (e(title),e(description),e(canonical),e(title),e(description),
       e(canonical),robots,e(GA_ID),e(GA_ID),e(local("assets","style.css")),
       e(local("assets","app.js")),e(local()),e(local()),e(local("apps")),
       e(local("about")),body,e(local("about")),e(local("privacy")),e(local("editorial-policy")))

def write(path, html):
    dest=SITE/path.strip("/")/"index.html" if path else SITE/"index.html"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(html,encoding="utf-8")
    return dest

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
    return rows

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
    if current:
        report="오늘 공개 정답 %d건 · 진행 및 보상 가능 여부는 원본 앱에서 확인"%current
    else:
        report="오늘 확인된 정답 없음 · 최근 7일 기록은 확인 가능"
    return '''<a class="appcard" href="%s" data-event="home_app_click" data-app="%s">
    <span class="appicon">%s</span><span><strong>%s</strong><small>%s</small>
    <span class="appstat">%s</span></span><span class="chevron">›</span></a>'''%(e(app_path(slug)),e(slug),icon,e(name),e(sub),e(report))

def breadcrumb(*nodes):
    links=[]
    for title,path in nodes:
        links.append(link(title,path))
    return '<nav class="breadcrumbs" aria-label="현재 위치">'+ ' <span aria-hidden="true">›</span> '.join(links)+'</nav>'

def heading(kicker,title,lead):
    return '<div class="section-head"><div class="eyebrow">%s</div><h1>%s</h1><p>%s</p></div>'%(e(kicker),e(title),e(lead))

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

    hero='''<section class="hero"><span class="eyebrow light">TODAY · QUIZPICK</span>
    <h1>앱테크 퀴즈,<br>정답은 여기서 찾아보세요.</h1>
    <p>토스·카카오뱅크 먼저. 앱을 선택하고 해당 회차의 정답을 확인하세요.</p>
    <div class="hero-date">한국시간 %s 기준 · 공개 정답 자료 %d건</div></section>'''%(e(TODAY.isoformat()),len(rows))
    homes=heading("1순위","먼저 확인할 퀴즈","회차별 정답은 앱 전용 페이지에서 확인할 수 있습니다.")
    homes+='<div class="featured">'+''.join(app_summary(x,byapp[x]) for x in p0)+'</div>'
    others=heading("다른 앱테크","추가 퀴즈","최근 7일 동안 공개 정답 자료가 확인된 앱만 보여드립니다.")
    others+='<div class="apps-grid">'+''.join(app_summary(x,byapp[x]) for x in remaining)+'</div>'
    others+='<p class="inline-action">'+link("전체 앱 보기 →",local("apps"))+'</p>'
    sections='<section class="section">'+homes+'</section><section class="section">'+others+'</section>'
    guide='''<section class="info"><h2>퀴즈픽 이용 방법</h2><p>앱 이름을 선택한 뒤 날짜와 회차를 확인하세요. 정답 상세에서 복사한 내용은 반드시 원본 앱에서 다시 확인해 주세요. 퀴즈는 마감·변경될 수 있으며 퀴즈픽이 포인트를 지급하지 않습니다.</p></section>'''
    homebody=hero+sections+guide
    write("",page("오늘의 토스·카카오뱅크 앱테크 퀴즈", "토스 행운퀴즈와 카카오뱅크 AI 이모지 퀴즈부터 날짜와 회차별 공개 정답을 확인하세요. 리워드는 원본 앱에서 제공합니다.",homebody,local()))

    allbody=breadcrumb(("홈",local()))+heading("QUIZ DIRECTORY","앱테크 퀴즈 전체 목록","최근 7일 정답 출처가 확인된 앱을 먼저 표시합니다. 과거 이벤트나 미확인 서비스는 현재 참여 가능하다고 표시하지 않습니다.")
    allbody+='<label class="finder">앱 이름 검색 <input type="search" id="app-search" placeholder="토스, 카카오뱅크, 캐시워크..." autocomplete="off"></label>'
    allbody+='<div class="apps-grid app-list">'+''.join(app_summary(x,byapp[x]) for x in apporder)+'</div>'
    allbody+='<div class="info"><h2>왜 모든 앱을 표시하지 않나요?</h2><p>종료된 이벤트와 운영 확인이 어려운 퀴즈를 현재 참여 가능한 것처럼 안내하지 않기 위해서입니다. 정답이 있는 앱도 보상 지급 여부는 앱에서 다시 확인해야 합니다.</p></div>'
    write("apps",page("앱테크 퀴즈 전체 목록","토스, 카카오뱅크, 캐시워크 등 공개 정답 자료가 확인된 앱 모음.",allbody,local("apps")))

    for slug in apporder:
        name,icon,_,instructions,subtitle=APPS[slug]
        arr=byapp[slug]
        dated=defaultdict(list)
        for q in arr:
            dated[q["date"]].append(q)
        appbody=breadcrumb(("홈",local()),("전체 앱",local("apps")))
        appbody+=heading(subtitle,icon+" "+name+" 퀴즈 정답","오늘의 회차와 지난 7일 공개 기록을 날짜별로 확인하세요.")
        if slug in p0:
            types=sorted(set(label(r) for r in arr))
            if types:
                appbody+='<p class="pills">'+''.join('<span>'+e(t)+'</span>' for t in types)+'</p>'
        appbody+='<section class="info"><h2>어디서 참여하나요?</h2><p>'+e(instructions)+'</p><p>공개 정답이 등록돼도 현재 회차가 열려 있거나 리워드가 남았다는 뜻은 아닙니다.</p></section>'
        appbody+='<section class="section">'+heading("날짜별 확인","퀴즈 날짜 선택","정답이 등록된 날짜만 표시합니다.")
        appbody+='<div class="days">'+quiz_group(slug,dated)+'</div></section>'
        appbody+='<p class="inline-action">'+link("다른 앱테크 퀴즈 둘러보기 →",local("apps"))+'</p>'
        write(app_path(slug).removeprefix(BASE+"/").strip("/"),
              page(name+" 오늘의 퀴즈 정답 · 날짜별 목록",name+"의 최근 회차, 공개 정답 기록 및 참여 방법.",appbody,app_path(slug)))

    for (slug,date),rs in byday.items():
        name=APPS[slug][0]
        rs.sort(key=lambda x: (x.get("time") or "",x["id"]),reverse=True)
        body=breadcrumb(("홈",local()),(name,app_path(slug)))
        body+=heading("DATE · "+date,name+" "+date+" 퀴즈 회차","날짜와 문제 요약을 비교하고 해당 정답 페이지를 선택하세요.")
        body+='<p class="notice">지난 회차 및 출처에 게시된 정보입니다. 현재 참여 가능 여부나 적립 보상을 보장하지 않습니다.</p>'
        body+='<div class="quizlist">'+''.join(item_card(x) for x in rs)+'</div>'
        body+='<p class="inline-action">'+link("← "+name+" 날짜 목록",app_path(slug))+'</p>'
        write(day_path(slug,date).removeprefix(BASE+"/").strip("/"),
              page(name+" "+date+" 문제별 정답 목록",name+"의 "+date+" 공개 문제와 회차를 선택하세요. 정답은 각 상세에서 표시됩니다.",body,day_path(slug,date),
                   noindex=len(rs)<=1))
        for row in rs:
            qpath=quiz_path(row)
            qtitle=label(row)+" "+row["date"]+" 정답"
            body=breadcrumb(("홈",local()),(name,app_path(slug)),(date,day_path(slug,date)))
            body+=heading(label(row),name+" "+row["date"]+" 정답 확인","회차: "+(row.get("time") or "출제시각 미확인")+" · "+state(row))
            body+='<section class="question-detail"><h2>문제 정보</h2><p>'+e(summary(row))+'</p></section>'
            body+='<section class="answer-detail"><div class="eyebrow">외부 공개 자료에 게시된 정답</div><div class="answer-value" id="answer-value">'+e(row["answer"])+'</div><button class="copybtn" type="button" data-copy-answer data-app="'+e(slug)+'">📋 정답 복사</button><p>원본 앱의 문제와 회차가 같은지 반드시 확인하세요.</p></section>'
            source=row.get("source_url","")
            body+='<section class="info"><h2>참여 방법과 확인 사항</h2><p>'+e(APPS[slug][3])+'</p>'
            body+='<p>정답 출처: '+e(row.get("source","외부 공개 자료"))+' · '+e(row.get("confidence_label","외부 미검증"))+'</p>'
            body+='<p>현재 회차 참여·지급 여부: 미확인. 보상은 원본 앱에서 지급되며 시간·대상·잔여 수량에 따라 달라질 수 있습니다.</p>'
            body+='<p>'+link("게시된 원문 확인 ↗",source,"source-link", 'target="_blank" rel="noopener noreferrer" data-event="source_open" data-app="'+e(slug)+'"')+'</p></section>'
            rec=[x for x in rs if x["id"]!=row["id"]][:3]
            if rec:
                body+='<section class="section">'+heading("RELATED","같은 날짜 다른 정답","다른 문제나 회차를 확인할 수 있습니다.")+'<div class="quizlist">'+''.join(item_card(x) for x in rec)+'</div></section>'
            body+='<p class="inline-action">'+link("← "+name+" 전체 회차",app_path(slug))+'</p>'
            write(qpath.removeprefix(BASE+"/").strip("/"),
                  page(qtitle+" · "+summary(row),name+" "+date+" "+label(row)+" 답을 확인하고 복사하세요. 원본 앱 회차와 보상을 확인하세요.",body,qpath,noindex=True))

    info_pages=[
      ("about","퀴즈픽 소개","퀴즈픽은 앱테크 퀴즈의 공개 정답 참고 자료와 참여 방법을 모아 제공하는 독립 서비스입니다. 토스·카카오뱅크를 먼저 보여주며, 각 운영사와 제휴하거나 이들로부터 리워드를 지급받는 서비스가 아닙니다."),
      ("privacy","개인정보 및 방문 통계 안내","이 웹사이트는 회원가입, 결제 또는 개인별 정답 제출 기록을 요구하지 않습니다. 방문 통계 목적으로 Google Analytics 4를 사용하여 페이지 방문과 버튼 이용 집계가 전송될 수 있습니다. 웹 브라우저 설정이나 광고·추적 차단 기능으로 분석을 제한할 수 있습니다. 개인정보 및 방문 분석 문의는 공개 GitHub 저장소의 이슈 기능을 이용할 수 있습니다."),
      ("editorial-policy","정답 검증·정정 기준","퀴즈픽은 원본 앱이 아닌 공개 자료를 참고합니다. 게시된 답은 변경될 수 있으며 원본 앱에서 최종 확인해야 합니다. 회차 마감·보상 지급 가능 여부를 앱에서 실시간 확인하지 않은 경우 '미확인'으로 표시합니다. 잘못된 답이나 출처 정정은 GitHub 저장소의 공개 이슈로 제보해 주세요."),
    ]
    for path,title,description in info_pages:
        text=breadcrumb(("홈",local()))+heading("QUIZPICK",title,description)
        text+='<p class="inline-action">'+link("GitHub 프로젝트와 정정 요청 ↗","https://github.com/Sean-messiah/quizpick-lite/issues","source-link",'target="_blank" rel="noopener noreferrer"')+'</p>'
        write(path,page(title,description,text,local(path)))

    urls=[local(),local("apps")]+[app_path(x) for x in apporder]
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
    (SITE/"robots.txt").write_text("User-agent: *\nAllow: /\nSitemap: "+absolute(local("sitemap.xml"))+"\n",encoding="utf-8")
    print("built v1:",len(rows),"quizzes,",len(apporder),"apps,",len(byday),"date pages")

if __name__=="__main__":
    main()
