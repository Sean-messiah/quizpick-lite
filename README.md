# 퀴즈픽 Lite — 앱테크 퀴즈·오늘의 참여 기록

공개 사이트: https://sean-messiah.github.io/quizpick-lite/
챌린지: https://sean-messiah.github.io/quizpick-lite/challenge/
앱테크 가이드: https://sean-messiah.github.io/quizpick-lite/guide/apptech-routine/

## 구현 기능 (2026-10-20)

- 분홍색 모바일 UI, 홈(토스·카카오뱅크 우선) → 앱별 페이지 → 날짜별 회차 → 정답 복사.
- 퀴즈픽에 실제 등록된 오늘의 퀴즈 체크리스트를 기본 화면으로 제공. 날짜별 참여 체크, 퀴즈별 실제 수령 수량과 단위(원/P/캐시/기타) 기록, 원화와 앱별 포인트 분리 집계, 연속 참여일 계산. 참가 가능성과 지급 여부는 보증하지 않음.
- 참여 개수×사용자 가정 원화 환산액 기반 1/30/100일 예상 계산기는 지급액 예측값이 아닌 임의 가정용 도구.
- 기존 50원/100원/금 0.1돈 목표는 접힌 '이전 기록'에서 그대로 열람/백업할 수 있음. 기존 데이터를 새 체크리스트 수익에 중복 합산하지 않음.
- 닉네임으로 시작하고 기록을 로컬 브라우저에 저장. JSON 백업·복원·삭제 제공.
- Supabase 프로젝트(quizpick)와 이메일 로그인 베타가 연결됨. 기존 기록은 로그인만으로 업로드되지 않고 이용자가 계정 병합을 선택한 경우에만 서버에 저장 시도. 앱별 참여 기록은 quizpick_daily_activities 테이블에 기록, 사용자별 RLS 적용. **실제 여러 기기 간 동기화는 아직 계정 실사용 테스트가 필요합니다.** 운영용 SMTP 설정 전까지 일반 공개 가입 제한.
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

## Supabase 계정 동기화 준비

- UI: site/assets/auth.js, site/auth-config.json (disabled)
- SQL: supabase/migrations/20261020_quizpick_challenge_auth.sql
- 상세 연결 절차: docs/QUIZPICK_SUPABASE_SETUP.md
- 공개 웹앱에 데이터베이스 비밀키를 넣지 않으며 본인 기록에만 접근하는 RLS 정책을 적용해야 합니다.

## 일별 체크리스트 v2 (2026-10-20)

- `scripts/build_site.py`가 검사된 정답만 `site/challenge-feed.json`으로 생성합니다. 문제 제목·날짜·회차 및 링크만 포함하고 정답 문자열과 사용자 기록은 포함하지 않습니다.
- `site/assets/daily-challenge.js`는 표시된 퀴즈를 직접 완료 체크하고 실제 수령 수량 및 단위를 기록합니다. 브라우저 키 `quizpick_daily_quizzes_v1`의 기존 사용자 기록은 페이지 생성 때 삭제되지 않습니다.
- `supabase/migrations/20261020_quizpick_daily_activity.sql`를 DB에 적용했으며 `public.quizpick_daily_activities`에 본인 기록만 접근 가능하도록 설정했습니다.
- `site/assets/auth.js`는 사용자 동의 후 새 일일 기록과 이전 목표를 각각 서버로 전송하며 다른 기기의 기록 불러오기 버튼을 제공합니다. 보안 확인 및 실제 로그인 브라우저에서의 동기화 시나리오 검증은 계속 필요합니다.
- 외부 리워드 포인트는 현금과 환산비가 같지 않을 수 있어 원화 합계에 더하지 않습니다. 30/100일 예상 수익은 사용자 입력값만 반영합니다.
