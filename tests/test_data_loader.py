from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

from menu_bot import data_loader as dl
from menu_bot.data_loader import ENCODING, DataStore

from conftest import write


def test_load_restaurants(store: DataStore):
    rs = store.restaurants
    assert len(rs) == 4
    first = rs[0]
    assert first.name == "가까운한식"
    assert first.walk_min == 3 and first.price == 1 and first.capacity == 4
    assert first.rain_ok is True
    assert "빠름" in first.tags


def test_bad_lines_skipped(tmp_path: Path):
    write(tmp_path / "restaurants.txt", (
        "# header\n"
        "정상집 | 한식 | 5 | 1 | 4 | 태그 | Y\n"
        "필드부족 | 한식 | 5\n"
        "숫자오류 | 한식 | 다섯 | 1 | 4 | 태그 | N\n"
        " | 한식 | 5 | 1 | 4 | 태그 | N\n"
        "\n"
    ))
    rs = dl.load_restaurants(tmp_path / "restaurants.txt")
    assert [r.name for r in rs] == ["정상집"]


def test_missing_and_empty_file(tmp_path: Path):
    assert dl.load_restaurants(tmp_path / "없는파일.txt") == []
    write(tmp_path / "empty.txt", "")
    assert dl.load_menus(tmp_path / "empty.txt") == []


def test_cp949_fallback(tmp_path: Path):
    p = tmp_path / "restaurants.txt"
    p.write_bytes("구형메모장집 | 한식 | 5 | 1 | 4 | 태그 | Y\n".encode("cp949"))
    rs = dl.load_restaurants(p)
    assert rs and rs[0].name == "구형메모장집"


def test_append_history_and_reload(store: DataStore):
    assert store.record_history("점심", "가까운한식")
    hist = store.history
    assert len(hist) == 1
    assert hist[0].choice == "가까운한식"
    assert hist[0].date == date.today().isoformat()


def test_append_suggestion_sanitizes_pipe(store: DataStore):
    assert store.add_suggestion("김OO", "신상|버거", "양식", "한줄\n평")
    s = store.suggestions
    assert len(s) == 1
    assert s[0].name == "신상/버거"
    assert "\n" not in s[0].comment


def test_suggestions_merge_into_pool(store: DataStore):
    store.add_suggestion("김OO", "신상버거", "양식", "가성비")
    pool = store.all_restaurants()
    names = [r.name for r in pool]
    assert "신상버거" in names
    merged = next(r for r in pool if r.name == "신상버거")
    assert merged.source == "suggestion"
    assert "직원추천" in merged.tags
    # 마스터와 같은 이름이면 중복 합류하지 않는다
    store.add_suggestion("이OO", "가까운한식", "한식", "또갓집")
    assert sum(1 for r in store.all_restaurants() if r.name == "가까운한식") == 1


def test_favorites_exclude_roundtrip(store: DataStore):
    store.set_favorite("가까운한식", True)
    assert "가까운한식" in store.favorites
    store.set_favorite("가까운한식", False)
    assert "가까운한식" not in store.favorites
    store.set_excluded("마라탕", True)
    assert "마라탕" in store.excluded


def test_weather_freshness(tmp_path: Path):
    p = tmp_path / "weather.txt"
    today = date.today().isoformat()
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    write(p, f"{today} | 비\n")
    assert dl.load_weather(p) == "비"
    write(p, f"{yesterday} | 비\n")
    assert dl.load_weather(p) is None  # 오래된 날씨는 무시
    write(p, "눈\n")
    assert dl.load_weather(p) == "눈"  # 날짜 없는 수동 형식
    write(p, "태풍\n")
    assert dl.load_weather(p) is None  # 알 수 없는 값


def test_mtime_reload(store: DataStore, data_dir: Path):
    assert len(store.restaurants) == 4
    import os
    import time
    write(data_dir / "restaurants.txt", "새집 | 한식 | 5 | 1 | 4 | 태그 | Y\n")
    # mtime 해상도 문제 방지
    future = time.time() + 10
    os.utime(data_dir / "restaurants.txt", (future, future))
    assert [r.name for r in store.restaurants] == ["새집"]


def test_personal_dir_split(tmp_path: Path, data_dir: Path):
    personal = tmp_path / "personal"
    personal.mkdir()
    store = DataStore(data_dir, personal_dir=personal)
    store.record_history("점심", "가까운한식")
    assert (personal / "history.txt").exists()
    store.set_favorite("가까운한식", True)
    assert (personal / "favorites.txt").exists()


def test_ensure_sample_data(tmp_path: Path):
    target = tmp_path / "fresh"
    assert dl.ensure_sample_data(target) is True
    assert (target / "restaurants.txt").exists()
    assert (target / "menus.txt").exists()
    raw = (target / "restaurants.txt").read_bytes()
    assert raw.startswith(b"\xef\xbb\xbf")  # UTF-8 BOM
    assert dl.ensure_sample_data(target) is False  # 두 번째는 첫 실행 아님
