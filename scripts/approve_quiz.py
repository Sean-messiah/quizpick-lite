#!/usr/bin/env python3
"""Manually approve a collected quiz only after human verification."""
import argparse
import json
import re
from pathlib import Path
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

SITE=Path(__file__).resolve().parents[1]/"site"
TODAY=datetime.now(timezone(timedelta(hours=9))).date().isoformat()
VALID_ID=re.compile(r"^[A-Za-z0-9_-]{4,100}$")
METHODS={"checked_original_app","checked_official_source"}

def candidates(feed, today=TODAY):
    seen=set()
    result=[]
    for q in feed.get("quizzes",[]):
        if not isinstance(q,dict):continue
        rid=q.get("id")
        if (not isinstance(rid,str) or not VALID_ID.fullmatch(rid)
                or rid in seen or q.get("date")!=today or not str(q.get("answer") or "").strip()):
            continue
        seen.add(rid)
        result.append(q)
    return sorted(result,key=lambda x:(str(x.get("app")),str(x.get("time") or ""),x["id"]))

def approve(feed,curated,quiz_id,expected_answer,verification,confirmation,today=TODAY):
    if confirmation!="APPROVE" or verification not in METHODS:
        raise ValueError("원본 앱 또는 공식 출처를 확인한 후 승인해야 합니다.")
    matches=[q for q in candidates(feed,today) if q["id"]==quiz_id]
    if len(matches)!=1:raise ValueError("오늘 등록된 유효한 퀴즈 ID가 없습니다.")
    q=dict(matches[0])
    if str(q.get("answer") or "").strip()!=expected_answer.strip():
        raise ValueError("확인한 정답이 수집된 참고 정답과 다릅니다.")
    if len(expected_answer)>350:raise ValueError("정답이 비정상적으로 깁니다.")
    link=q.get("source_url")
    if not isinstance(link,str) or urlparse(link).scheme!="https" or not urlparse(link).hostname:
        raise ValueError("HTTPS 출처 URL이 필요합니다.")
    if str(q.get("question_hint") or "").strip() in ("","문제 문구 확인 불가","문제 요약 확인 필요"):
        raise ValueError("문제 내용을 식별할 수 없습니다.")
    old=curated.get("quizzes",[])
    if not isinstance(old,list) or len(old)>=5000:raise ValueError("검수 데이터 형식 또는 보관량 오류")
    if any(item.get("id")==quiz_id for item in old):
        raise ValueError("이미 검수된 문제입니다. 다시 발행할 수 없습니다.")
    q.update(reviewed=True,verification_method=verification,reviewed_at_kst=datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds"),reward_status="NOT_CHECKED",confidence_label="관리자 검수 참고 정답")
    output=dict(curated)
    output["quizzes"]=old+[q]
    return output,q

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--list",action="store_true")
    p.add_argument("--quiz-id",default="")
    p.add_argument("--expected-answer",default="")
    p.add_argument("--verification",default="")
    p.add_argument("--confirm",default="")
    args=p.parse_args()
    feed=json.loads((SITE/"data.json").read_text(encoding="utf-8"))
    curated=json.loads((SITE/"manual-quizzes.json").read_text(encoding="utf-8"))
    if args.list:
        done={q["id"] for q in curated.get("quizzes",[])}
        print("오늘의 승인 대기 목록 — 자동 승인이 아닙니다.")
        for q in candidates(feed):
            if q["id"] not in done:
                print(f'{q["id"]} | {q.get("app")} | {q.get("question_hint")} | {q.get("source_url")}')
        return
    next_feed,q=approve(feed,curated,args.quiz_id,args.expected_answer,args.verification,args.confirm)
    (SITE/"manual-quizzes.json").write_text(json.dumps(next_feed,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f'검수 승인: {q["id"]} / {q["app"]} / {q["date"]}')

if __name__=="__main__":main()
