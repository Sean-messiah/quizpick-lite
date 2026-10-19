# 퀴즈픽 v1.0 — 앱테크 퀴즈 큐레이션 및 수익화 설계
기준: 2026-10-19 KST
상태: 기획 확정 제안. 현재 서비스 리뉴얼 배포 및 광고 승인은 별도 작업.

## 제품 방향
- 토스(행운퀴즈, 두근두근 1등찍기) 첫 번째, 카카오뱅크(AI 이모지, OX) 두 번째 카드.
- 현재 출제 확인과 리워드 제도 확인을 분리하고, 실제 앱에서 회차 및 보상 지급 가능 여부를 확인하지 않은 상태에서 '지금 적립 가능'이라고 표시하지 않는다.
- 홈에는 정답 미노출. 홈 → 앱별 허브 → 당일 회차 선택 → 개별 정답 상세 → 원본 앱 이동.
- 퀴즈가 1개면 불필요한 중간 목록 단계를 생략. 광고만을 위한 페이지 분할 금지.
- 서비스를 운영하는 퀴즈픽이 포인트를 지급하지 않음. 원본 앱에서만 지급.

## 최초 참고 사이트 검토
1. https://rewardtip.com/리워드-퀴즈-정답/ : 통합 허브와 카테고리 이동
2. https://rewardtip.com/앱테크-퀴즈-정답-모음/ : 검색 유입용 페이지 + 관련 퀴즈 추천
3. https://rewardtip.com/토스-정답-확인하기/ : 참여 방법·정답·다른 퀴즈·연관 정보
4. https://rewardtip.com/돈버는퀴즈-캐시워크-정답/ : 최근 문제와 상세 안내
5. https://rewardtip.com/오퀴즈-정답/ : 회차별 정보
6. https://rewardtip.com/퀴즈타임-정답/ : 브랜드 단발성 이벤트 다수
7. https://rewardtip.com/올원뱅크-디깅퀴즈/ : 최근 기록과 참여 안내
8. https://rewardtip.com/국민은행-kb-퀴즈-정답/ : KB 관련 정답
9. https://rewardtip.com/쏠퀴즈-정답/ : 신한 관련 정답
10. https://rewardtip.com/모니스쿨-정답/ : 월간 교시별 정답
11. https://rewardtip.com/모니모-오늘의영어/ : 영어 퀴즈
12. https://rewardtip.com/기후동행퀴즈정답/ : 과거 리워드 안내 (현재 공식 지급 종료)
초기 허브의 비트버니, 캐시닥·타임스프레드, 하나원큐 일부 링크는 직접 열람 오류로 확인하지 못함. 교차자료 확인 후 공개 대상 결정. 참고 사이트의 표현/디자인/DB 대량 복제 금지.

## 최근 출제 근거와 선별
### 최우선
- 토스: 10월 19일 퀴즈 기록. https://quiz.jjyu.co.kr/quiz/toss-lucky/2026-10-19/
- 카카오뱅크 AI 이모지 및 OX: 10월 19일 문제 기록 및 랜덤 캐시 지급 구조. https://quizbells.com/quiz/kakaobank/monthly
- 카뱅 OX 10/19: https://1bang.kr/posts/event/카카오뱅크-ox-퀴즈-10-19-정답-292326
- 카뱅 공식 OX 광고 안내: https://ad.kakaobank.com/adp/ee644b38fd3fb44031a0738bc27e74aae62e47c2e5643fffc05d322a98214828

### 추가 채택 후보
- 캐시워크: 10/19 공개 기록 + 공식 돈버는퀴즈 광고 서비스 https://cashwalk.com/business/ads/quiz
- OK캐쉬백 오퀴즈: 10/19 출제 + 랜덤 포인트 https://www.job-post.co.kr/news/articleView.html?idxno=232980
- 신한 SOL·SOL페이: 10/19 출제 및 포인트 https://quiz.jjyu.co.kr/quiz/shinhan-sol/2026-10-19/
- 비트버니: 10/19 문제·코인 https://www.namdonews.com/news/articleView.html?idxno=926453
- 케이뱅크 AI 퀴즈: 10/19 출제 및 상금형 운영 https://catchwon.com/kbank-ai-quiz/20261019/
- H.Point: 10/19 문제 및 포인트 https://catchwon.com/hpoint-quiz/20261019/
- 모니모 모니스쿨: 10월 진행 중인 교시형 퀴즈/젤리 지급. https://ibim0.tistory.com/1661
- KB스타뱅킹·KB Pay, NH, 캐시닥·타임스프레드: 10월 문제 기록은 있으나 현재 회차 및 지급 조건 재검증 후 공개.
- 카카오페이/버즈빌 및 각종 브랜드 초성퀴즈: 일회성 이벤트인 경우 캠페인별 현재 진행·리워드 확인이 선행돼야 함.

### 보류 또는 제외
- 기후행동 기회소득: 경기도 공식 안내에 2026년 8월 활동분부터 리워드 지급 종료. https://www.ggaction.or.kr/ . 현행 리워드 퀴즈로 표시 금지.
- 당근: 과거 이벤트는 있으나 현재 운영 중인 정답형 리워드 이벤트 미검증. 메인 제외.
- 과거/마감된 브랜드 퀴즈, 공개 출처만 있고 앱 지급 제도를 확인 못 한 이벤트.

## IA 및 URL
- / : 검색, P0 토스·카뱅 카드, 추가 앱의 최근 출제 카드. 정답 미노출.
- /toss/ : 토스 앱 허브 + 행운퀴즈와 두근두근1등찍기 분리.
- /kakaobank/ : 카뱅 AI 08시/12시/20시 + OX 별도 탭.
- /quiz/{app}/{YYYY-MM-DD}/ : 날짜/회차별 목록; 정답 미노출.
- /quiz/{app}/{YYYY-MM-DD}/{id}/ : 정답, 정답 복사, 확인시각, 근거, 앱 참여 링크, 연관 정답.
- /apps/ : 전체 앱 목록과 조회 필터. 종료/미확인 퀴즈는 기본 검색 화면에 숨김.
- /guide/{app}/ : 충분한 고유 설명이 있는 앱별 참여·리워드 가이드.
- /about, /privacy, /contact, /editorial-policy : 서비스·프라이버시·정정 규칙.

## 정답 상태와 데이터 필드
- 출제확인과 적립가능성은 별개.
- 공개 정답 상태: VERIFIED_ANSWER / UNCONFIRMED / NO_QUESTION / HISTORICAL.
- 리워드 상태: IN_APP_CONFIRMED / PUBLIC_REWARD_PROGRAM / NOT_CHECKED / ENDED.
- IN_APP_CONFIRMED는 앱 실제 이벤트 화면을 확인했을 때만 수동 적용; 앱의 실시간 접근이 없는 자동 수집은 못 씀.
- 데이터: id, app_id, quiz_type, date_kst, round_label, question_summary, answer, source_urls, official_url, verification_method, verified_at_kst, reward_kind, reward_status, publication_status, participation_deadline, correction_note.
- 한국시각 날짜 검증, 회차 구분, 중복제거, 최근 검증일, 보상 소진 미확인 표시.
- 저작권·약관·robots 점검. HTTP 403 차단 우회 금지. 다른 사이트 전체 문구/이미지 복제 금지.

## 화면 및 광고
1. 홈: 서비스 카드, 문제 건수/업데이트 시각, 인기 앱, 퀴즈 소개. 정답 미노출.
2. 앱 허브: 앱 내 참여 경로, 참여 가능 조건, 날짜/회차 목록. 광고는 유익한 콘텐츠 뒤에 노출.
3. 회차 목록: 각 문제 제목/출제시각/상태, 상세 정답으로 명확하게 이동. 여러 문제가 없으면 생략.
4. 상세: 정답/복사 버튼을 쉽게 찾게 배치. 인증시각, 앱 원본 이동, 주의/FAQ, 관련 퀴즈. 광고가 복사·이동 버튼을 가리지 않도록.
- AdSense 승인 전 광고 위치는 실제 광고 없이 구성. 광고는 명시적으로 구분, 클릭 유도 불가.
- 페이지가 너무 짧거나 같은 텍스트만 복사하는 SEO 도어웨이/씬 콘텐츠를 생성하지 않음.
- 공식 앱 방문 전 퀴즈픽에서 실제 현금·포인트 지급을 보장한다고 쓰지 않음.

## 개발 방식
- 현 GitHub Pages 유지. Python + Jinja2 또는 Astro를 사용해 앱 허브/날짜/회차별 정적 HTML 생성 후 배포.
- 승인된 공급처 수집→정규화→검증→편집 검수→정적 페이지 빌드→GitHub Pages.
- 토스의 단기 이벤트는 2시간 갱신만으로 부족. 접근 허가된 소스 또는 수동 관리자 업데이트 경로 확보 필요.
- GA4 G-3Y68828WYZ 유지. home_app_click, app_quiz_click, answer_copy, official_app_click 측정. 사용자 계정정보 전송 금지.
- SEO: 고유 메타 제목/설명, canonical, 오픈그래프, sitemap.xml, breadcrumbs, 검색엔진 등록, 필요시 도메인.
- 수익화: 자체 도메인 연결 권장, 콘텐츠/정책/개인정보 안내 점검, AdSense 심사 후 ads.txt와 광고 배치. 수익은 유효 페이지뷰 및 페이지 RPM에 따라 변동, 보장 불가.
- 정책: https://support.google.com/adsense/answer/1346295 ; https://support.google.com/adsense/answer/48182 ; https://developers.google.com/search/docs/essentials/spam-policies

## 순서와 완료 기준
1. P0 앱 및 퀴즈 유형/회차 데이터 정규화, 홈페이지 Top2 정렬, 정답 노출 제거.
2. 앱별 허브·날짜 목록·개별 상세 페이지 정적 URL 만들기.
3. 원본 앱 참여 버튼, 회차/정답 복사, 상태 표기, 뒤로가기 및 모바일 테스트.
4. 최근 출제 및 리워드 검증된 캐시워크·오퀴즈·신한·비트버니·케이뱅크·H.Point 추가.
5. 원본성 있는 가이드 콘텐츠/SEO·정책 페이지 → AdSense 신청 → 광고 배치 검수.
6. GA4에서 화면별 이탈률, 문제 상세 도달률, 원본 앱 이동률 측정해 개선.
기준: 홈 정답 미노출, 상세 정답 접근 명료, 지난 회차 명시, 미확인 퀴즈 진행중 표시 금지, 광고와 탐색 버튼 분리, 모바일 실접속 정상, 출처와 정정경로 제공.
