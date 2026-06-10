# 점심메뉴 추천 알림봇 — 개발 계획

> 기획안: [점심메뉴_추천_알림봇_기획안.md](점심메뉴_추천_알림봇_기획안.md) · 작성일: 2026-06-10
>
> **상태(2026-06-10): v0.1.0 완성.** M0~M3 계획 기능 + 기획 리뷰 보완(기획안 12장) 전부 구현,
> 테스트 28건 통과, exe 빌드/검증 완료. 남은 일: 실데이터 정리, 보안팀 화이트리스트 협의(기획안 8장).

---

## 1. 기술 스택 확정

기획안의 1순위 추천에 따라 **Python + PyInstaller**로 진행한다.

| 구성 | 선택 | 이유 |
|------|------|------|
| 언어/런타임 | Python 3.12 (개발 PC에 설치 확인됨) | 개발 속도, txt 파싱·룰렛 로직 구현 용이 |
| GUI | **tkinter** (표준 라이브러리) | 외부 의존성 0 → exe 용량 최소·망분리 반입 부담 없음. 픽셀아트 PNG는 `PhotoImage`로 표시 가능 |
| 데스크톱 알림 | **winotify** | 순수 Python, 의존성 없음, Windows 10/11 토스트 지원 |
| 트레이 아이콘 | **pystray** (+Pillow) | 트레이 상주 + 우클릭 메뉴. Pillow는 픽셀아트 에셋 생성에도 사용 |
| 패키징 | **PyInstaller** `--onefile --noconsole` | 단일 exe, 무설치 실행 |
| 데이터 | txt (파이프 구분, UTF-8 BOM) — 기획안 5장 스키마 그대로 | |

> 백신 오탐 리스크(기획안 11장): MVP exe가 나오는 즉시 사내 보안팀 화이트리스트 협의 시작. 통과 실패 시 C#/.NET 전환 — 데이터 계층(txt)은 그대로 재사용.

## 2. 프로젝트 구조

```
D:\menu_bot\
├── src\menu_bot\          # 애플리케이션 패키지
│   ├── __init__.py        # 버전 정보
│   ├── main.py            # 엔트리포인트 (창 + 트레이)
│   ├── config.py          # config.txt 로드/저장
│   ├── data_loader.py     # restaurants/menus/suggestions/history txt 파싱
│   ├── recommender.py     # 필터 → 쿨다운 감점 → 가중 랜덤 (기획안 6장)
│   ├── notifier.py        # 11:30/17:30 토스트 알림 스케줄
│   └── ui\                # tkinter 화면 (메인/룰렛/등록/이력/설정)
├── data\                  # txt 데이터 (배포 시 exe 옆에 동봉)
│   ├── restaurants.txt
│   ├── menus.txt
│   ├── suggestions.txt
│   ├── history.txt
│   └── config.txt
├── assets\                # 픽셀아트 PNG (기획안 7-A)
├── scripts\
│   ├── make_assets.py     # JB 로고·밥봇 마스코트 픽셀아트 생성
│   └── build.ps1          # PyInstaller 빌드 스크립트
├── tests\                 # pytest 단위 테스트 (파서·추천 로직 중심)
├── requirements.txt       # 런타임 의존성
├── requirements-dev.txt   # pyinstaller, pytest
└── DEVELOPMENT_PLAN.md
```

## 3. 마일스톤 (기획안 10장 로드맵 구체화)

### M0. 환경설정 + 데이터 — ✅ 완료
- [x] Python 3.12 / git 확인
- [x] venv 생성, 의존성 설치, git 저장소 초기화
- [x] 프로젝트 골격 + 샘플 txt 데이터 생성
- [x] `make_assets.py`로 픽셀아트 에셋 생성

### M1. MVP (목표 2주) — F1, F2, F5, A1, A2, A7
1. **데이터 계층**: txt 파서(주석/빈줄/오류줄 스킵 + error.log), config 로드, history append
2. **추천 엔진**: 모드별 후보 수집 → 필터(카테고리·가격·인원·도보) → 쿨다운 감점 → 가중 랜덤. *pytest로 검증*
3. **UI**: 메인 창([점심][저녁][회식] + 날씨 토글 + 카테고리 칩) → 룰렛 애니메이션 → 결과 카드 → history 기록
4. **알림**: 트레이 상주 + 지정 시각 토스트("오늘 뭐 먹지?") → 클릭 시 창 표시
5. **패키징**: PyInstaller 단일 exe + 첫 실행 시 샘플 데이터 자동 생성(온보딩)
6. **검증**: exe를 깨끗한 PC에서 실행 테스트 → 보안팀 화이트리스트 협의 착수

### M2. 확장 (2주) — F3, F4, A3, A4
- 날씨 토글/`weather.txt` 연동 → 비올때OK·도보 제한 필터
- 직원 추천 폼 → suggestions.txt append(파일 락) → 후보 합류
- 그룹 투표 모드(후보 3~5개, 다수결/거부권)
- 이력/통계 화면(월간 캘린더, TOP5)

### M3. 안정화 (1주) — A5, A6, A8~A10
- 즐겨찾기/제외, 모드별 기본값, txt 자동 리로드(mtime 감지), 검색, 결과 클립보드 복사
- 코드사이닝/화이트리스트 마무리, 배포 패키징(공유폴더 data + 각 PC exe)

## 4. 망분리 대응 (빌드·배포 관점)

- **빌드는 인터넷 되는 개발 PC(이 PC)에서** 수행하고, 산출물 exe + `data\` 폴더만 사내망 반입. → 사내망에서 패키지 반입 절차 불필요.
- 사내망에서 직접 빌드해야 할 경우 대비: `pip download -r requirements.txt -d wheels\`로 휠 일괄 다운로드 후 반입 (M1 패키징 단계에서 정리).
- 날씨·지도 API 미사용: 수동 토글 + txt 사전 입력 (기획안 8장).

## 5. 의존성 (최소주의)

| 패키지 | 용도 | 비고 |
|--------|------|------|
| winotify | 토스트 알림 | 의존성 없음 |
| pystray | 트레이 아이콘 | Pillow 필요 |
| Pillow | 트레이 아이콘 이미지 + 에셋 생성 | |
| pyinstaller (dev) | exe 패키징 | |
| pytest (dev) | 테스트 | |

GUI(tkinter), 스케줄(threading.Timer), 파싱(표준 io)은 전부 표준 라이브러리로 해결 → exe 용량·오탐 표면적 최소화.
