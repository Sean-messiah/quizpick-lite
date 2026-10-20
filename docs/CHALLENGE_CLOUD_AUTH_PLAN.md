# 퀴즈픽 100일 챌린지: 체험형 MVP → 계정 동기화 / 미니게임·장보기 연동

기준: 2026-10-20. 상태: MVP 배포, 로그인·서버 동기화는 미구현.

## 제품 정의
- 사용자가 다른 앱에서 스스로 적립했다고 확인한 금액을 기록하는 **습관 추적기**.
- 퀴즈픽에서 현금·포인트·금을 지급하지 않으며 광고를 클릭/보는 행위를 적립 조건으로 삼지 않음.
- 닉네임+로컬 스토리지로 회원가입 없는 사용 체험 제공. 실제 계정은 향후 별도 인증.
- 예시: 50원×100일=5,000원, 100원×100일=10,000원.
- 금 0.1돈=0.375g 목표는 사용자가 **구매 예산**을 설정하고 기록한 원화 누적액에 대해 진행률 계산. 금·원화 자동 환전 없음.
- 매일 한국시간 날짜별 챌린지 1회 기록. 같은 날짜 기록 수정·취소 허용; 기록 중복 불허.
- 이용자의 개인 금액·닉네임은 분석 이벤트에 포함하지 않음.
- localStorage key: `quizpick_challenge_v1`, data model `{version:1,nickname,goals:{fifty|hundred|gold:{startDate,goalWon,entries:{"YYYY-MM-DD":amount}}}}`.
- 기록 JSON 백업, 삭제 기능 제공. 브라우저 데이터 삭제·기기 교체 시 현재 동기화되지 않음.

## 다음 단계: 간편 계정 가입
1. Supabase Auth 이메일 매직링크 또는 적절한 소셜 로그인으로 실제 소유자 인증. 닉네임 입력만으로는 '계정 가입'으로 안내하지 않음.
2. 로그인 후 사용자 동의를 받고 로컬 기록을 서버 데이터로 1회 이관.
3. Supabase PostgreSQL에 profiles, challenge_goals, challenge_entries 3개 테이블을 생성하고 사용자별 RLS 활성화.
4. 이미 다른 장치에서 기록한 날짜가 있으면 자동 중복 적립하지 않고 충돌 해결 UI 제공.
5. 삭제 요청과 로그아웃, 데이터 내려받기, 개인정보·보존기간 안내.
6. Auth 도메인과 서비스 도메인의 인증 상태가 안전하게 유지되는지 모바일 테스트. 서로 다른 프로젝트 간 SSO는 신중하게 설계.
7. 이메일·전화번호 같은 개인 식별정보는 GA4 이벤트로 전송하지 않음.

## 백엔드 테이블 초안
- profiles: user_id(PK, references auth.users), nickname, created_at, updated_at
- challenge_goals: id(UUID PK), user_id, kind(fifty|hundred|gold), start_date, goal_amount_won, created_at
  - unique(user_id,kind)
- challenge_entries: id(UUID PK), goal_id, user_id, entry_date(KST local date), amount_won(1~1,000,000), updated_at
  - unique(goal_id,entry_date)
- RLS: 모든 select/insert/update/delete 는 authenticated user의 auth.uid()와 user_id가 동일한 경우만 허용. challenge_entries가 참조하는 goal 소유권도 확인.
- 클라이언트에서 '나의 적립 = 서버가 검증한 보상'으로 해석할 수 있는 이름 사용 금지.

## 교차 링크 / 별도 미니게임·장보기
- 실제 배포 URL이 확인되기 전에는 페이지에 빈 링크, 추정 URL, 공식 제휴처럼 보이는 문구를 넣지 않음.
- 현재 챌린지에 미니게임·장보기 '준비 중' 안내 카드만 표시.
- 게임은 별도 주소로 정적 배포하고 내부 이동 배너 제공; '보너스 적립을 받으려면 광고를 보라' 등의 유도 금지.
- 장보기 서비스도 실제 공개 URL 확인 후 동일한 메뉴/배너 registry를 사용해 연결.
- 향후 공통 브랜드, 로그인, 개인정보 정책, 출처 표기 규칙을 중앙 설계. 개별 서비스별 GA4 이벤트로 banner_source, destination_id 등 **비식별** 정보만 측정.
- 초기 성과 측정: 챌린지 첫 시작률, 1일·7일 재방문, 100일 이내 체크 일수, 도전 미완료 비율, 배너를 통한 자발적 이동률.
- 앱들이 서로 광고 노출 수를 늘리기 위해 자동으로 새로고침·이동하거나 클릭에 보상 부여하지 않음.

## SEO 운영
- 인덱싱 가능한 단일 챌린지 소개 페이지 및 독창적 참여 가이드(/guide/apptech-routine/).
- 개인별 진척도·기록 내용은 정적 HTML/검색 색인에 넣지 않음. 검색봇에 닉네임이나 누적액을 공개하지 않음.
- BreadCrumbList 링크와 정식 URL, 정확한 사이트맵.
- 매 빌드마다 변경되지 않은 페이지를 '오늘 수정됨'으로 표시하지 않음.
- 짧고 유사한 50원/100원/금 도전 페이지를 수백 개 생성하지 않음.

## 수집 확대 운영
- 기존 허용 출처 크롤러는 유지. 접근 거부된 사이트 403 우회/재시도 공격 금지.
- `site/manual-quizzes.json`에는 앱·문제·정답·출처·날짜·회차가 검증된 자료만 등록.
- `reviewed:true`가 없는 자료는 자동 게시하지 않음. 실서비스 원문 표시 권한·이용약관 별도 확인.
- 새 수집원의 데이터가 들어오면 `scripts/build_site.py`가 지원 앱(비트버니, H.Point, 케이뱅크, 모니모 포함)의 앱/회차/정답 페이지 생성.
- 운영 확대 시 공급자별 요청 성공률, 업데이트 지연, 중복, 출처 충돌 로그와 검수 큐 설계.

## 보안·광고
- 로컬 기록은 사용자 브라우저에 저장되며 서버 검증 결과가 아님.
- 실제 가입·동기화에는 인증과 RLS 필수. 공개 GitHub에는 비밀키 저장 금지.
- 애드센스/일반 광고 클릭·조회와 챌린지 체크/목표 달성을 연동하지 않음.
- 참고: https://support.google.com/adsense/answer/2660562 및 https://developers.google.com/search/docs/essentials/spam-policies
