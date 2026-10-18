# 퀴즈픽 Lite

앱테크 퀴즈 정답을 모아 보여주는 무료 정적 웹 MVP입니다.

- 정적 모바일 웹사이트: `site/index.html`
- JSON 데이터: `site/data.json`
- 공개 페이지 수집기: `scraper/collect.py`
- 자동 업데이트: `.github/workflows/crawl.yml` (2시간 간격, GitHub Actions 예약 실행은 지연될 수 있음)
- 파서 테스트: `tests/test_collect.py`

## 시작

1. **Actions**에서 **QuizPick Lite - public quiz index refresh → Run workflow**를 눌러 첫 크롤링을 실행하세요.
2. Actions에서 수집 결과 및 커밋 여부를 확인합니다. 저장소 **Settings → Actions → General → Workflow permissions**에서 필요하면 **Read and write permissions**로 변경하세요.
3. Cloudflare Pages에서 이 GitHub 저장소를 연결하고 빌드 명령은 비운 채 **출력 폴더 `site`**를 선택하면 공개 웹사이트를 만들 수 있습니다.
4. 무료 플랜의 빌드·실행량, 사이트 약관 및 데이터 재사용 조건을 확인하세요.

## 데이터 및 출처

초기 수집처는 공개된 살보픽 날짜별 퀴즈 페이지 한 곳입니다. HTML 변경, 로봇 정책, 요청 실패에 따라 수집이 중단될 수 있으며 원본 앱의 정답 여부는 별도 검증하지 않습니다. 원문 링크를 함께 제공하며 긴 문제를 그대로 전재하지 않습니다. robots 허용은 콘텐츠 복제 허가가 아닙니다.

`site/data.json`은 처음에는 빈 배열입니다. 최초 실제 수집 성공 후에만 데이터가 기록됩니다. 정답을 찾지 못하면 저장된 데이터는 보존됩니다.

로컬 실행:
```bash
pip install -r requirements.txt
python -m unittest discover -s tests -v
python scraper/collect.py
python -m http.server 8000 -d site
```

공개 저장소이므로 비밀번호/API 키를 커밋하지 마세요.

모바일 UI의 필터·검색·복사 기능은 실제 데이터가 들어온 뒤 사용할 수 있습니다.
