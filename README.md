# 퀴즈픽 Lite — 앱테크 퀴즈 허브 & 100일 챌린지

공개 사이트: https://sean-messiah.github.io/quizpick-lite/
챌린지: https://sean-messiah.github.io/quizpick-lite/challenge/
앱테크 가이드: https://sean-messiah.github.io/quizpick-lite/guide/apptech-routine/

## 구현 기능 (2026-10-20)

- 분홍색 모바일 UI, 홈(토스·카카오뱅크 우선) → 앱별 페이지 → 날짜별 회차 → 정답 복사.
- 100일 챌린지: 50원/100원/금 0.1돈(0.375g) 목표. 사용자가 실제 모은 금액을 하루 한 번 직접 기록하며 누적액·달성률·연속 체크·7/30/100일 마일스톤 확인.
- 닉네임으로 시작하고 기록을 로컬 브라우저에만 저장. JSON 백업·복원·삭제 제공. 실제 회원가입·서버 동기화는 미구현.
- 퀴즈픽은 사용자에게 포인트·현금·금을 지급하지 않습니다. 챌린지 입력 금액은 자체 기록이며 원본 앱 적립이 검증된 값이 아닙니다.
- SEO: 실제 탐색 URL, 정규 주소(canonical), 사이트맵, BreadcrumbList 구조화 데이터, 앱테크 루틴 독창적인 가이드 페이지.
- 44개 카탈로그 목록 중 실제 공개 정답이 확인된 앱만 기본 표시. 원본 앱의 이벤트 지급 여부는 보증하지 않음.
- 기존 공개 출처 기반 수집: scraper/collect.py 및 scraper/collect_focus.py, 정상 허용된 수집만 주기적으로 실행.
- QUIZDAY의 35개 경로는 GitHub Actions 서버에서 HTTP 403을 반환하여 자동 작업 비활성화. 차단 우회 금지.
- site/manual-quizzes.json: 검수된 짧은 문제·정답 참조를 입력하는 데이터 소스. reviewed=true, 정상 HTTPS 출처와 필수 필드를 갖춘 자료만 생성기에 반영.
- 비트버니·H.Point·케이뱅크·모니모는 수집원 확보 후 앱별 페이지를 자동으로 만들 수 있도록 지원 준비. 현재 자동 수집되는 것은 아님.
- Github Pages 배포 시 Python 테스트 + JavaScript 구문 검사 + 수집 설정 JSON 검사 + 정적 페이지 생성 및 검증.
- GA4 측정 ID G-3Y68828WYZ; 닉네임/기록 금액을 분석 이벤트로 전송하지 않음.

## 수집 확대

운영자의 검수 데이터는 site/manual-quizzes.json에 입력. 새 레코드는 ID, app, date, question_hint, answer, source_url, reviewed 필드와 실제 이용 허가/출처 검증이 필요합니다. reviewed=false 는 게시되지 않습니다.
지원 앱 목록에 없으면 scripts/build_site.py 의 APPS 항목을 먼저 추가하고 검사합니다.
자동 수집 확대는 데이터 공급자의 이용 허가와 robots/약관 및 요청 제한을 검증한 뒤에만 진행합니다.

## 향후 기능

- 실제 이메일 매직링크 또는 소셜 로그인을 통한 회원가입 및 클라우드 동기화. DB에 본인 소유 기록만 보이는 RLS 정책 필수.
- 미니게임과 장보기 서비스는 각기 따로 배포. 공개 주소가 확정되면 상호 배너 링크 연결. 현재는 준비 중 안내만 표기.
- 설계: docs/CHALLENGE_CLOUD_AUTH_PLAN.md

## 로컬 검증

1. python -m pip install -r requirements.txt
2. python -m unittest discover -s tests -v
3. node --check site/assets/challenge.js
4. python scripts/build_site.py
5. python -m http.server 8000 -d site

외부 공개 자료의 접근 허용은 콘텐츠 재게시 권한을 의미하지 않습니다. 광고 클릭이나 광고 시청은 챌린지 실적과 전혀 연관시키지 않습니다.
