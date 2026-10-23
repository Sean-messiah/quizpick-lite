# 퀴즈픽 v1.2 웹 푸시 알림 운영

## 배포 구성 (2026-10-23)
- 사이트: https://sean-messiah.github.io/quizpick-lite/
- 구독: https://sean-messiah.github.io/quizpick-lite/alerts/
- Supabase Edge Function: `quizpick-push` (VAPID Web Push, 공개 구독 설정 API + 비공개 디스패처)
- Supabase DB: `quizpick_push_subscriptions`, `quizpick_push_delivery`; 양쪽 RLS ON, anon/authenticated DB 조회·갱신 권한 없음
- Edge cron: `quizpick-reviewed-push-15m`, 15분마다 검수 승인된 신규 퀴즈 검사
- 서비스워커: `site/sw.js`; manifest: `site/manifest.webmanifest`
- PWA 아이콘 SVG. 기기별 설치 UI 지원 범위는 브라우저 정책에 따름.

## 수신 흐름
1. 갤럭시/Chrome 등 호환 브라우저에서 `/alerts/` 접속. 퀴즈 서비스 선택.
2. 동의 확인 후 '알림 받기' 버튼 직접 클릭 → 브라우저 OS 알림 권한 허용.
3. 클라이언트는 Web PushSubscription(endpoint, p256dh, auth)과 랜덤 기기 토큰을 HTTPS Edge Function으로 제출.
4. 서버는 공개키와 구독에 필요한 브라우저 정보를 저장하고 기기 토큰은 SHA-256 해시만 저장. 전화번호·이메일·닉네임 불필요.
5. 검수한 새 퀴즈를 최초 발견하면 선택한 서비스 구독자에게 **정답 내용을 포함한 푸시**를 발송. 앱 내 회차와 정답은 사용자가 확인해야 함.
6. '알림 구독 해지'는 서버 구독 행(발송 기록 포함)을 삭제하고 브라우저 푸시 구독도 해지. 테스트 알림은 사용자 클릭 시 15분에 1회까지.

## 발송 대상 승인 기준
**외부 자동 크롤링 결과만으로 푸시하지 않습니다.** `site/manual-quizzes.json`에서 사람 검수한 다음 조건 모두 충족해야 합니다:
- `reviewed: true`
- `reviewed_at_kst` 필드에 ISO 8601 시간대 포함 시각 (예: `2026-10-23T13:30:00+09:00`)
- `date`는 당일 또는 전일 한국시간이며, 검수 시각이 24시간 이내
- `id`는 고유하며 지원 앱 slug, `answer` 내용 존재
- 사용자 **구독 이후 검수된 회차**만 발송; 구독 전 과거 퀴즈 발송 금지
- 동일 기기+회차 조합은 DB unique claim으로 중복 방지

예시 검수 항목(실제 문제 또는 정답 아님):
```json
{
  "id": "example-curated-20261023-round1",
  "app": "toss",
  "date": "2026-10-23",
  "question_hint": "검수한 문제 요약",
  "answer": "실제 검수된 정답만",
  "source_url": "https://publisher.example/verified",
  "reviewed": true,
  "reviewed_at_kst": "2026-10-23T13:30:00+09:00"
}
```
**예시 항목을 실제 데이터에 추가하지 마세요.** 출처·표현 이용권을 확인한 실제 문제만 수동 검수해 공개합니다. 현재 검수 완료된 항목이 없다면 자동 발송 0건이 정상입니다.

## 개인정보와 보안
- 전화번호·이메일·카카오 계정 연결은 하지 않음. 알림톡·카카오 채널 발송도 아직 하지 않음.
- HTTP API는 `Origin` 검사, 구독 유효성 검사, 단말 토큰 소유권 검사를 수행. 익명 요청의 IP별 대규모 남용 방지는 운영 트래픽이 늘면 추가해야 함.
- Edge Function에서는 서버 서비스 키만 사용하고, 클라이언트에는 VAPID 공개키만 노출함.
- VAPID 비밀키와 크론 인증키는 Supabase Vault에 암호화 저장. GitHub, 앱 JS, 빌드 로그에 비밀키를 넣지 않음.
- `public.quizpick_push_runtime_secret()` RPC는 `service_role`에만 EXECUTE 권한이 있음.
- 발송 불능(404/410) 구독은 서버에서 삭제함.
- 수신 동의가 거부되거나 알림 지원 안 되는 브라우저에서는 푸시 미구독 상태 유지.
- 브라우저 알림과 서버 구독은 별개의 상태이므로 OS 수준으로 차단하면 알림이 표시되지 않을 수 있음.

## 운영 확인
- 공개 설정 GET: `GET /functions/v1/quizpick-push` → `enabled:true` & VAPID 공개키
- 유효하지 않은 구독 등록 요청 → HTTP 400 또는 403
- 크론: `select jobname,schedule,active from cron.job where jobname='quizpick-reviewed-push-15m'`
- 발송 응답: `net._http_response`의 HTTP 200과 `sent,failed,approved` 값 확인
- 갤럭시 실기기: **동의→권한→등록→테스트 수신→해지** 절차의 최종 검증이 필요. 브라우저별 실행 여부를 과장하지 마세요.
- KST 승인 날짜·세션, URL 이동, 캐시 무효화 확인
- 약관/정책에 따라 수신 동의 문구와 보존 기간을 서비스 운영자가 최종 검토해야 함.

## GitHub 관리자 수동 검수 (v1.3)
- 관리 링크: https://github.com/Sean-messiah/quizpick-lite/actions/workflows/approve-quiz.yml
- 저장소 쓰기 권한이 있는 운영자가 수동으로 실행합니다.
1. Run workflow → approval=LIST_ONLY 실행 → 로그에서 후보 quiz_id·문제·출처 확인
2. 원본 앱 또는 공식 자료에서 문제와 정답을 대조합니다. 공개 자동 수집 결과만으로 승인하지 않습니다.
3. Run workflow 재실행: quiz_id와 직접 확인한 expected_answer, verification=checked_original_app 또는 checked_official_source, approval=APPROVE를 입력합니다.
4. 승인은 site/manual-quizzes.json에 reviewed=true, KST 검수 시각과 확인 경로를 기록하고 GitHub Pages 배포 후 15분 주기로 발송 대상으로 검사됩니다.
5. 과거 날짜·틀린 정답·중복 승인·검수되지 않은 항목은 자동 차단됩니다. 실제 리워드 보유 여부는 별개입니다.
검수 스크립트: scripts/approve_quiz.py / 테스트: tests/test_approve_quiz.py
