from __future__ import annotations

import random
from datetime import date, timedelta
from pathlib import Path

from menu_bot import recommender as rec
from menu_bot.data_loader import DataStore
from menu_bot.recommender import (
    MODE_DINING, MODE_LUNCH, MODE_MENU, Query,
    collect_candidates, collect_with_relaxation, pick_slots, weighted_pick,
)

from conftest import write


def names(cands):
    return sorted(c.name for c in cands)


def test_lunch_no_filter(store: DataStore):
    cands = collect_candidates(store, Query(mode=MODE_LUNCH))
    assert names(cands) == ["가까운한식", "먼일식", "중간중식", "회식고기집"]


def test_category_filter(store: DataStore):
    cands = collect_candidates(store, Query(mode=MODE_LUNCH, categories={"일식"}))
    assert names(cands) == ["먼일식"]


def test_rain_filter(store: DataStore):
    # 비: rain_ok=Y 이거나 도보 10분 이내
    cands = collect_candidates(store, Query(mode=MODE_LUNCH, weather="비", walk_limit=10))
    assert "먼일식" not in names(cands)          # 15분, rain_ok=N
    assert "가까운한식" in names(cands)
    rain_ok = next(c for c in cands if c.name == "가까운한식")
    assert rain_ok.weight > 1.0                  # 비올때OK 가중


def test_dining_capacity_and_budget(store: DataStore):
    cands = collect_candidates(store, Query(mode=MODE_DINING, people=20))
    assert names(cands) == ["회식고기집"]
    cands = collect_candidates(store, Query(mode=MODE_DINING, people=10, max_price=2))
    assert names(cands) == ["중간중식"]


def test_menu_mode_spice(store: DataStore):
    cands = collect_candidates(store, Query(mode=MODE_MENU, max_spice=1))
    assert names(cands) == ["돈카츠"]


def test_keyword_search(store: DataStore):
    cands = collect_candidates(store, Query(mode=MODE_LUNCH, keyword="단체석"))
    assert names(cands) == ["회식고기집"]


def test_cooldown_penalty_and_type_split(store: DataStore, data_dir: Path):
    today = date.today().isoformat()
    old = (date.today() - timedelta(days=10)).isoformat()
    write(data_dir / "history.txt",
          f"{today} | 점심 | 가까운한식\n"
          f"{today} | 메뉴 | 김치찌개\n"
          f"{old} | 점심 | 중간중식\n")
    cands = collect_candidates(store, Query(mode=MODE_LUNCH, cooldown_days=3))
    by_name = {c.name: c for c in cands}
    assert by_name["가까운한식"].weight < 0.5       # 최근 선택 → 감점
    assert by_name["중간중식"].weight == 1.0        # 오래된 선택 → 영향 없음
    # 메뉴 이력은 식당 쿨다운에 영향 없어야 함 (유형 분리)
    menu_cands = collect_candidates(store, Query(mode=MODE_MENU, cooldown_days=3))
    menu_by_name = {c.name: c for c in menu_cands}
    assert menu_by_name["김치찌개"].weight < 0.5
    assert menu_by_name["돈카츠"].weight == 1.0


def test_excluded_hard_filter(store: DataStore):
    store.set_excluded("먼일식", True)
    cands = collect_candidates(store, Query(mode=MODE_LUNCH))
    assert "먼일식" not in names(cands)


def test_favorite_boost(store: DataStore):
    store.set_favorite("가까운한식", True)
    cands = collect_candidates(store, Query(mode=MODE_LUNCH))
    fav = next(c for c in cands if c.name == "가까운한식")
    assert fav.weight > 1.0


def test_relaxation_stages(store: DataStore):
    # 비 + 일식: 먼일식(15분, N)뿐 → 도보 완화(20분)로 살아남
    q = Query(mode=MODE_LUNCH, categories={"일식"}, weather="비", walk_limit=10)
    cands, notes = collect_with_relaxation(store, q)
    assert names(cands) == ["먼일식"]
    assert notes  # 완화 사실이 사용자에게 안내됨


def test_relaxation_zero_result(tmp_path: Path):
    write(tmp_path / "restaurants.txt", "# empty\n")
    write(tmp_path / "menus.txt", "# empty\n")
    store = DataStore(tmp_path)
    cands, notes = collect_with_relaxation(store, Query(mode=MODE_LUNCH))
    assert cands == []


def test_weighted_pick_and_slots(store: DataStore):
    cands = collect_candidates(store, Query(mode=MODE_LUNCH))
    rng = random.Random(42)
    pick = weighted_pick(cands, rng)
    assert pick is not None and pick.name in names(cands)
    assert weighted_pick([], rng) is None
    slots = pick_slots(cands, n=3, rng=rng)
    assert len(slots) == 3
    assert len({s.name for s in slots}) == 3  # 비복원(중복 없음)
    assert len(pick_slots(cands, n=99, rng=rng)) == len(cands)


def test_zero_weight_candidates_still_pickable(store: DataStore):
    cands = collect_candidates(store, Query(mode=MODE_LUNCH))
    for c in cands:
        c.weight = 0.0
    assert weighted_pick(cands, random.Random(1)) is not None
