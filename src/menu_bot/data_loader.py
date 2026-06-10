"""txt 데이터 읽기/쓰기.

- 구분자 파이프(|), '#' 시작 줄과 빈 줄은 무시.
- 잘못된 줄은 건너뛰고 error.log 에 경고만 남긴다(프로그램은 죽지 않는다).
- 쓰기(append)는 공유 폴더 동시 사용을 고려해 잠금 실패 시 재시도한다.
"""
from __future__ import annotations

import logging
import time
from datetime import date, datetime
from pathlib import Path

from .models import HistoryEntry, MenuItem, Restaurant, Suggestion
from .paths import writable_app_dir

log = logging.getLogger(__name__)

ENCODING = "utf-8-sig"  # 메모장 호환(UTF-8 BOM)

FILE_RESTAURANTS = "restaurants.txt"
FILE_MENUS = "menus.txt"
FILE_SUGGESTIONS = "suggestions.txt"
FILE_HISTORY = "history.txt"
FILE_FAVORITES = "favorites.txt"
FILE_EXCLUDE = "exclude.txt"
FILE_WEATHER = "weather.txt"

WEATHER_VALUES = ("맑음", "비", "눈")


def setup_error_log() -> None:
    """error.log 파일 핸들러를 루트 로거에 연결(WARNING 이상만)."""
    handler = logging.FileHandler(writable_app_dir() / "error.log", encoding="utf-8")
    handler.setLevel(logging.WARNING)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    logging.getLogger().addHandler(handler)
    logging.getLogger().setLevel(logging.INFO)


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding=ENCODING)
    except UnicodeDecodeError:
        log.warning("%s: UTF-8 해석 실패, cp949로 재시도", path.name)
        return path.read_text(encoding="cp949", errors="replace")


def _data_lines(path: Path) -> list[tuple[int, list[str]]]:
    """(행번호, 파이프 분리 필드 목록) — 주석/빈 줄 제외."""
    if not path.exists():
        return []
    rows = []
    for lineno, raw in enumerate(_read_text(path).splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        rows.append((lineno, [f.strip() for f in line.split("|")]))
    return rows


def _skip(path: Path, lineno: int, reason: str) -> None:
    log.warning("%s %d행 건너뜀: %s", path.name, lineno, reason)


# ---------------------------------------------------------------- 읽기

def load_restaurants(path: Path) -> list[Restaurant]:
    out = []
    for lineno, f in _data_lines(path):
        if len(f) < 7 or not f[0]:
            _skip(path, lineno, f"필드 7개 필요(현재 {len(f)}개)")
            continue
        try:
            out.append(Restaurant(
                name=f[0], category=f[1] or "기타",
                walk_min=int(f[2]), price=int(f[3]), capacity=int(f[4]),
                tags=[t.strip() for t in f[5].split(",") if t.strip()],
                rain_ok=f[6].upper().startswith("Y"),
            ))
        except ValueError as e:
            _skip(path, lineno, f"숫자 필드 해석 불가({e})")
    return out


def load_menus(path: Path) -> list[MenuItem]:
    out = []
    for lineno, f in _data_lines(path):
        if len(f) < 3 or not f[0]:
            _skip(path, lineno, f"필드 3개 필요(현재 {len(f)}개)")
            continue
        try:
            out.append(MenuItem(name=f[0], category=f[1] or "기타", spice=int(f[2])))
        except ValueError as e:
            _skip(path, lineno, f"맵기 해석 불가({e})")
    return out


def load_suggestions(path: Path) -> list[Suggestion]:
    out = []
    for lineno, f in _data_lines(path):
        if len(f) < 4 or not f[2]:
            _skip(path, lineno, f"필드 4개 이상 필요(현재 {len(f)}개)")
            continue
        out.append(Suggestion(date=f[0], author=f[1], name=f[2], category=f[3],
                              comment=f[4] if len(f) > 4 else ""))
    return out


def load_history(path: Path) -> list[HistoryEntry]:
    out = []
    for lineno, f in _data_lines(path):
        if len(f) < 3 or not f[0]:
            _skip(path, lineno, f"필드 3개 필요(현재 {len(f)}개)")
            continue
        try:
            datetime.strptime(f[0], "%Y-%m-%d")
        except ValueError:
            _skip(path, lineno, f"날짜 형식 오류 '{f[0]}'")
            continue
        out.append(HistoryEntry(date=f[0], mode=f[1], choice=f[2]))
    return out


def load_name_list(path: Path) -> list[str]:
    """즐겨찾기/제외 목록 — 한 줄에 이름 하나."""
    return [f[0] for _, f in _data_lines(path) if f[0]]


def load_weather(path: Path) -> str | None:
    """weather.txt 첫 데이터 줄을 읽는다 (사내 인트라넷 연동용, F3).

    형식: `날짜 | 상태` 또는 `상태` 단독 (상태 = 맑음|비|눈).
    날짜가 있으면 오늘 날짜일 때만 유효 — 어제의 '비'로 계속 우천 필터가
    걸리는 것을 막는다. UI 수동 토글이 항상 이 값보다 우선한다.
    """
    rows = _data_lines(path)
    if not rows:
        return None
    lineno, fields_ = rows[0]
    if len(fields_) >= 2:
        file_date, value = fields_[0], fields_[1]
        if file_date != date.today().isoformat():
            log.info("%s: 날짜(%s)가 오늘이 아니어서 무시", path.name, file_date)
            return None
    else:
        value = fields_[0]
    if value not in WEATHER_VALUES:
        _skip(path, lineno, f"날씨 값은 {WEATHER_VALUES} 중 하나여야 함: '{value}'")
        return None
    return value


# ---------------------------------------------------------------- 쓰기

def _append_line(path: Path, line: str, retries: int = 5, delay: float = 0.3) -> bool:
    """파일 끝에 한 줄 추가. 공유 폴더 잠금 충돌 시 재시도. 성공 여부 반환."""
    for attempt in range(retries):
        try:
            new_file = not path.exists()
            with open(path, "a", encoding=ENCODING if new_file else "utf-8", newline="") as fp:
                fp.write(line.rstrip("\n") + "\n")
            return True
        except PermissionError:
            time.sleep(delay * (attempt + 1))
        except OSError as e:
            log.warning("%s 쓰기 실패: %s", path.name, e)
            return False
    log.warning("%s 쓰기 실패: 파일이 계속 잠겨 있음", path.name)
    return False


def append_history(path: Path, mode: str, choice: str, on_date: date | None = None) -> bool:
    d = (on_date or date.today()).isoformat()
    return _append_line(path, f"{d} | {mode} | {choice}")


def append_suggestion(path: Path, author: str, name: str, category: str, comment: str) -> bool:
    def clean(s: str) -> str:
        return s.replace("|", "/").replace("\n", " ").strip()
    d = date.today().isoformat()
    return _append_line(path, f"{d} | {clean(author)} | {clean(name)} | {clean(category)} | {clean(comment)}")


def save_name_list(path: Path, header: str, names: list[str]) -> None:
    lines = [f"# {header}"] + list(dict.fromkeys(names))  # 중복 제거, 순서 유지
    path.write_text("\n".join(lines) + "\n", encoding=ENCODING)


# ---------------------------------------------------------------- 샘플 데이터(첫 실행 온보딩)

SAMPLE_RESTAURANTS = """\
# 이름 | 카테고리 | 도보분 | 가격대(1~3) | 인원수용 | 태그 | 비올때OK(Y/N)
한솥도시락 | 한식 | 3 | 1 | 4 | 도시락,혼밥,빠름 | Y
교다이야 | 일식 | 8 | 2 | 6 | 라멘,줄있음 | N
백제정육식당 | 한식 | 12 | 3 | 30 | 회식,단체석,고기 | N
진주집 | 한식 | 7 | 2 | 10 | 콩국수,여름,웨이팅 | N
유레카분식 | 분식 | 4 | 1 | 8 | 김밥,빠름,혼밥 | Y
홍콩반점 | 중식 | 6 | 1 | 12 | 짜장면,단체 | Y
샐러디 | 양식 | 5 | 2 | 4 | 샐러드,건강,포장 | Y
스시히로 | 일식 | 10 | 3 | 8 | 초밥,점심특선 | N
원조닭갈비 | 한식 | 9 | 2 | 20 | 회식,단체석,매움 | N
파스타뮤 | 양식 | 11 | 2 | 6 | 파스타,분위기 | N
"""

SAMPLE_MENUS = """\
# 메뉴 | 카테고리 | 맵기(0~3)
김치찌개 | 한식 | 2
된장찌개 | 한식 | 1
제육볶음 | 한식 | 2
비빔밥 | 한식 | 1
마라탕 | 중식 | 3
짜장면 | 중식 | 0
짬뽕 | 중식 | 2
돈카츠 | 일식 | 0
초밥 | 일식 | 0
라멘 | 일식 | 1
파스타 | 양식 | 0
햄버거 | 양식 | 0
샐러드 | 양식 | 0
떡볶이 | 분식 | 2
김밥 | 분식 | 0
부대찌개 | 한식 | 2
"""

_SAMPLE_FILES = {
    FILE_RESTAURANTS: SAMPLE_RESTAURANTS,
    FILE_MENUS: SAMPLE_MENUS,
    FILE_SUGGESTIONS: "# 등록일 | 등록자 | 이름 | 카테고리 | 한줄평\n",
    FILE_HISTORY: "# 날짜 | 모드 | 선택결과\n",
    FILE_FAVORITES: "# 즐겨찾기 (한 줄에 식당/메뉴 이름 하나)\n",
    FILE_EXCLUDE: "# 제외 목록 (한 줄에 식당/메뉴 이름 하나)\n",
}


def ensure_sample_data(data_dir: Path, personal_dir: Path | None = None) -> bool:
    """데이터 폴더/파일이 없으면 샘플 생성. 새로 만들었으면 True(=첫 실행)."""
    personal_dir = personal_dir or data_dir
    first_run = not (data_dir / FILE_RESTAURANTS).exists()
    data_dir.mkdir(parents=True, exist_ok=True)
    personal_dir.mkdir(parents=True, exist_ok=True)
    personal = (FILE_HISTORY, FILE_FAVORITES, FILE_EXCLUDE)
    for name, content in _SAMPLE_FILES.items():
        p = (personal_dir if name in personal else data_dir) / name
        if not p.exists():
            p.write_text(content, encoding=ENCODING)
    return first_run


# ---------------------------------------------------------------- DataStore

class DataStore:
    """txt 데이터 캐시. mtime 변경 시 자동 리로드(A8).

    - data_dir: 공유 데이터(restaurants/menus/suggestions/weather) — 공유 폴더 가능
    - personal_dir: 개인 데이터(history/favorites/exclude) — 쿨다운·즐겨찾기는
      개인의 것이므로 공유하면 의미가 깨진다. 기본은 data_dir와 동일.
    - 공유 폴더 단절(OSError) 시 마지막 성공 캐시로 동작한다.
    """

    PERSONAL_FILES = (FILE_HISTORY, FILE_FAVORITES, FILE_EXCLUDE)

    def __init__(self, data_dir: Path, personal_dir: Path | None = None):
        self.data_dir = data_dir
        self.personal_dir = personal_dir or data_dir
        self._cache: dict[str, tuple[float, object]] = {}

    def _dir_for(self, filename: str) -> Path:
        return self.personal_dir if filename in self.PERSONAL_FILES else self.data_dir

    def _load(self, filename: str, loader):
        path = self._dir_for(filename) / filename
        cached = self._cache.get(filename)
        try:
            mtime = path.stat().st_mtime if path.exists() else -1.0
            if cached and cached[0] == mtime:
                return cached[1]
            value = loader(path)
        except OSError as e:
            if cached:
                log.warning("%s 읽기 실패(%s) — 마지막 캐시로 동작", filename, e)
                return cached[1]
            log.warning("%s 읽기 실패(%s) — 빈 목록으로 동작", filename, e)
            return []
        self._cache[filename] = (mtime, value)
        return value

    @property
    def restaurants(self) -> list[Restaurant]:
        return self._load(FILE_RESTAURANTS, load_restaurants)

    @property
    def menus(self) -> list[MenuItem]:
        return self._load(FILE_MENUS, load_menus)

    @property
    def suggestions(self) -> list[Suggestion]:
        return self._load(FILE_SUGGESTIONS, load_suggestions)

    @property
    def history(self) -> list[HistoryEntry]:
        return self._load(FILE_HISTORY, load_history)

    @property
    def favorites(self) -> list[str]:
        return self._load(FILE_FAVORITES, load_name_list)

    @property
    def excluded(self) -> list[str]:
        return self._load(FILE_EXCLUDE, load_name_list)

    @property
    def weather_file(self) -> str | None:
        return self._load(FILE_WEATHER, load_weather)

    def all_restaurants(self) -> list[Restaurant]:
        """마스터 + 직원 추천(기본값 보정, '직원추천' 태그)을 합친 후보 풀."""
        merged = list(self.restaurants)
        known = {r.name for r in merged}
        for s in self.suggestions:
            if s.name in known:
                continue
            known.add(s.name)
            merged.append(Restaurant(
                name=s.name, category=s.category or "기타",
                tags=["직원추천"] + ([s.comment] if s.comment else []),
                source="suggestion",
            ))
        return merged

    def record_history(self, mode: str, choice: str) -> bool:
        ok = append_history(self._dir_for(FILE_HISTORY) / FILE_HISTORY, mode, choice)
        self._cache.pop(FILE_HISTORY, None)
        return ok

    def add_suggestion(self, author: str, name: str, category: str, comment: str) -> bool:
        ok = append_suggestion(self.data_dir / FILE_SUGGESTIONS, author, name, category, comment)
        self._cache.pop(FILE_SUGGESTIONS, None)
        return ok

    def set_favorite(self, name: str, on: bool) -> None:
        favs = [f for f in self.favorites if f != name]
        if on:
            favs.append(name)
        save_name_list(self._dir_for(FILE_FAVORITES) / FILE_FAVORITES, "즐겨찾기 (한 줄에 이름 하나)", favs)
        self._cache.pop(FILE_FAVORITES, None)

    def set_excluded(self, name: str, on: bool) -> None:
        ex = [e for e in self.excluded if e != name]
        if on:
            ex.append(name)
        save_name_list(self._dir_for(FILE_EXCLUDE) / FILE_EXCLUDE, "제외 목록 (한 줄에 이름 하나)", ex)
        self._cache.pop(FILE_EXCLUDE, None)
