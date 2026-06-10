# 🍙 밥봇 JB — 점심/저녁 메뉴 추천 알림봇

사내(여의도) 망분리 PC용 데스크톱 알림봇. 외부 API·DB 없이 **txt 파일 + 단일 exe**로 동작한다.

- 기획: [점심메뉴_추천_알림봇_기획안.md](점심메뉴_추천_알림봇_기획안.md)
- 개발 계획: [DEVELOPMENT_PLAN.md](DEVELOPMENT_PLAN.md)

## 주요 기능 (v0.1.0)

| 기능 | 설명 |
|------|------|
| 🎰 룰렛 추천 | 점심/저녁/회식/메뉴 모드별 가중 랜덤 룰렛 (애니메이션 + 마스코트 표정) |
| 🍖 회식장소 추천 | 인원수·예산(가격대 1~3) 조건 필터 |
| 🌧️ 날씨 연동 | 수동 토글 또는 `weather.txt`(오늘 날짜만 유효) — 우천 시 가까운 곳·비올때OK 우대 |
| ⏰ 알림 | 11:30/17:30(설정 가능) "오늘 뭐 먹지?" 토스트, 놓친 알림 캐치업 |
| 🔁 중복 방지 | 최근 N일 선택은 감점(쿨다운) — 메뉴/식당 이력 분리 매칭 |
| 🗳️ 그룹 투표 | 후보 3~5개 + 다수결/거부권 |
| ✍️ 직원 추천 | 폼 등록 → `suggestions.txt` append → 즉시 후보 합류 |
| 📊 이력/통계 | 이번 달 사용량·TOP5·최근 기록 |
| ⭐/🚫 | 즐겨찾기 가중(×1.6) / 제외 목록(하드 필터) |
| 📋 복사 | "오늘 점심: ○○ (한식·도보 5분)" 클립보드 복사 |

창을 닫아도 트레이에 상주하며, 중복 실행 시 기존 창이 올라온다. 시작프로그램 등록은 설정 탭 토글로.

## 데이터 (메모장으로 수정 가능, UTF-8)

`data\` 폴더 — 파이프(`|`) 구분, `#` 줄은 주석. 파일이 없으면 첫 실행 시 샘플 자동 생성.

```
restaurants.txt  이름 | 카테고리 | 도보분 | 가격대(1~3) | 인원수용 | 태그 | 비올때OK(Y/N)
menus.txt        메뉴 | 카테고리 | 맵기(0~3)
suggestions.txt  등록일 | 등록자 | 이름 | 카테고리 | 한줄평   (앱이 append)
history.txt      날짜 | 모드 | 선택결과                       (개인 데이터)
favorites.txt / exclude.txt   한 줄에 이름 하나               (개인 데이터)
weather.txt      날짜 | 맑음|비|눈   (선택 — 인트라넷 연동용)
```

설정은 exe 옆 `config.txt`(자동 생성). `data_path`=공유 데이터 폴더, `personal_path`=개인 데이터 폴더(비우면 동일). 잘못된 데이터 줄은 건너뛰고 `error.log`에 기록된다.

## 개발

```powershell
python -m venv .venv
.venv\Scripts\pip install -r requirements-dev.txt
.venv\Scripts\python -m pytest            # 테스트
.venv\Scripts\python scripts\make_assets.py   # 픽셀아트 에셋 재생성
.venv\Scripts\python -c "import sys; sys.path.insert(0,'src'); from menu_bot.main import main; main()"  # 실행
```

## 빌드 & 배포

```powershell
powershell -File scripts\build.ps1   # → dist\BapBotJB.exe (~17MB)
```

- 검증: `BapBotJB.exe --check` (exit 0이면 정상)
- 배포: exe는 **각 PC에**, `data\`는 공유 폴더 가능(개인 파일은 `personal_path`로 분리 권장)
- 사내망 반입 전 **보안팀 백신 화이트리스트 협의 필수** (PyInstaller 오탐 리스크 — 기획안 8장)
- 사내망에서 직접 빌드해야 하면: `pip download -r requirements-dev.txt -d wheels\` 후 휠 반입

## 구조

```
src\menu_bot\
├── main.py            엔트리 (--check 헤드리스 검증 모드)
├── config.py          config.txt 로드/저장, 경로 해석
├── data_loader.py     txt 파서·append·DataStore(mtime 리로드, 캐시 폴백)
├── recommender.py     필터 → 쿨다운 감점 → 가중 랜덤, 단계적 완화
├── stats.py           이력 통계
├── notifier.py        토스트 알림 폴링 스케줄러
├── tray.py            pystray 트레이 상주
├── singleinstance.py  mutex + 로컬 소켓 IPC
├── autostart.py       시작프로그램 바로가기
└── ui\                tkinter 탭들 + 룰렛 캔버스 + 테마
```
