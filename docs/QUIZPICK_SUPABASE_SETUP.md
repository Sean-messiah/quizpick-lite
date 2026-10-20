# 퀴즈픽 Supabase 계정 및 클라우드 동기화 설정

상태: 2026-10-20 기준 Supabase에 아직 프로젝트가 없어 비활성. 기존 챌린지는 로컬 저장으로 계속 무료 이용 가능.

## 프로젝트 준비
1. 사용자의 조직을 확인하고 무료 프로젝트 생성 여부와 비용을 확인합니다. 추가 비용이 발생한다면 동의를 받습니다.
2. Supabase Auth → Email 활성화 및 URL Configuration:
   - Site URL: https://sean-messiah.github.io/quizpick-lite/challenge/
   - Allowed Redirect URL: https://sean-messiah.github.io/quizpick-lite/challenge/
3. 서버 DB에 supabase/migrations/20261020_quizpick_challenge_auth.sql을 적용합니다.
4. Security Advisors로 세 테이블 RLS 활성화 및 소유자 접근 정책을 검사합니다.
5. 다른 계정 2개로 사용자 간 읽기/수정/삭제가 차단되는지 검사합니다.
6. 공개 가능한 Supabase Project API URL과 sb_publishable_ 키만 site/auth-config.json에 기입합니다.
7. enabled 값을 true로 전환하고 GitHub Pages 배포 후 실기기에서 이메일 링크 인증 및 데이터 이관을 확인합니다.
8. 기본 이메일 발송 제한을 확인하고 운영용 SMTP/스팸대응이 필요할 수 있습니다.
9. 개인정보처리방침에 실제 운영자 연락처, 수집/보존/삭제와 계정 탈퇴 절차를 고지합니다.

## 사용자 기록 이관 정책
- 닉네임은 회원가입이 아닙니다. 연결 전까지 데이터는 해당 기기의 브라우저에만 존재합니다.
- 이메일 로그인 후에도 기록은 자동으로 클라우드에 전송하지 않습니다.
- 이용자가 명시적으로 '이 기기 기록 계정에 병합'을 누르면 업로드합니다.
- 같은 날짜+같은 도전의 충돌은 명시적으로 승인한 로컬 기록이 우선하며 다른 서버 날짜는 유지합니다.
- 이후 동기화를 활성화하면 변경 시마다 클라우드 저장을 시도하고 실패한 경우 실패 안내를 표시합니다.
- 계정 기록을 로컬에 가져오는 작업도 사용자의 확인 후 진행합니다.
- 계정 기록 삭제 기능은 챌린지 데이터만 삭제합니다. Supabase 인증 계정 자체의 탈퇴는 별도 운영 절차가 필요합니다.
- 로그아웃해도 로컬 기록은 남습니다. 공용기기는 로컬 기록도 별도 삭제해야 합니다.
- GA4에 이메일·닉네임·실제 입력 금액을 보내지 않습니다.

## 보안
- Backend 테이블: quizpick_profiles, quizpick_goals, quizpick_entries. 본인 소유 행만 접근하는 RLS.
- 인증 계정 확인은 auth.uid() 와 user_id 일치 여부로 처리하며 anonymous 계정은 별도 차단.
- 사이트에는 Supabase publishable key만 공개하고 권한 상승용 키는 사용하지 않습니다.
- 세션 토큰을 서비스간 URL 쿼리로 전달하지 않습니다.
- 게임/장보기 사이트의 실제 URL이 확인되면 상호 이동 배너만 먼저 연결합니다.

## QA
- disabled configuration: 이메일 입력 폼 숨김, 로컬 챌린지 정상 사용.
- enabled configuration: 로그인 링크, 세션 유지, 로컬 병합, 다중 기기 가져오기, 계정 간 접근 차단, 로그아웃/삭제/오류 상태 확인.
- 새로고침과 네트워크 단절을 포함한 데이터 동기화 테스트 후 일반 사용자에게 공개.

관련 문서: https://supabase.com/docs/guides/auth/auth-email-passwordless
관련 문서: https://supabase.com/docs/guides/database/postgres/row-level-security
