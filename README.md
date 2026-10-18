# 퀴즈픽 Lite — 앱테크 퀴즈 정보 허브

무료 정적 웹사이트: https://sean-messiah.github.io/quizpick-lite/

## 현재 구현 현황 (2026-10-19)

- `site/catalog.json`: 국내 앱테크 퀴즈·리워드 관련 **42개 항목**의 목록과 공개 출처 링크를 정리했습니다. 일부 항목은 현재 운영/정답 공개 여부를 확인 중입니다.
- `site/index.html`: 모바일 퀴즈 정답 검색·앱별 필터·정답 복사, 전체 앱 목록 펼치기, 공개 출처 이동.
- `site/data.json`: 실제 수집된 정답만 표시합니다. 출처는 앱 운영사의 공식 API가 아닌 외부 공개 페이지이며 정답은 미검증입니다.
- `scraper/collect.py`: 살보픽 공개 페이지를 2시간 간격 확인.
- `scraper/collect_focus.py`: 카카오뱅크 AI이모지·토스 퀴즈의 공개 정보 수집.
- `scraper/collect_expanded.py`: QUIZDAY의 35개 공개 월간 경로 테스트용 수집기. **GitHub Actions 서버에서 35개 요청 모두 HTTP 403**을 받아 현재 자동 실행을 비활성화했습니다. 차단 우회 금지.
- `.github/workflows/crawl.yml`: 정상 동작 확인된 수집기만 정기 실행.
- `.github/workflows/crawl-expanded.yml`: 문제 원인 확인을 위한 수동 실행만 허용.
- `.github/workflows/deploy-pages.yml`: 정답 JSON 갱신 후 GitHub Pages 배포.
- Google Analytics GA4 측정 ID는 `site/index.html`에 설치되어 있습니다.

## 유의점

**42개 앱이 모두 자동 수집되는 것은 아닙니다.** 실제 정답 수집은 일부 항목에만 연결되어 있으며, 홈페이지 카탈로그의 '출처 보기'는 수동 확인용 링크입니다. '당근 퀴즈'는 지속 운영되는 정답형 리워드 이벤트의 공개 근거가 아직 확인되지 않아 '확인 대기'로 표시합니다.

공개 페이지의 robots 허용은 콘텐츠 재게시 권한을 의미하지 않습니다. 웹사이트 이용약관 및 저작권을 확인하고 접근거부 HTTP 403을 우회하지 않습니다. 정답은 원본 앱에서 최종 확인하세요.

## 로컬 개발

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python scraper/collect.py
python scraper/collect_focus.py
python -m http.server 8000 -d site
```

GitHub 저장소에 비밀번호와 비공개 API 키를 업로드하지 마세요.
