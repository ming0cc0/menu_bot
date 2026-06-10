"""추천 엔진 (기획안 6장).

후보 수집 → 필터 → 쿨다운 감점 → 즐겨찾기 가중 → 가중 랜덤.
완전 제외가 아니라 '감점'을 기본으로 하여 후보 고갈을 막는다.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field, replace
from datetime import date, timedelta

from .data_loader import DataStore
from .models import MenuItem, Restaurant

MODE_LUNCH = "점심"
MODE_DINNER = "저녁"
MODE_DINING = "회식"
MODE_MENU = "메뉴"

COOLDOWN_PENALTY = 0.15   # 최근 선택 가중치 배수
FAVORITE_BOOST = 1.6      # 즐겨찾기 가중치 배수


@dataclass
class Query:
    mode: str = MODE_LUNCH
    categories: set[str] = field(default_factory=set)  # 빈 set = 전체
    weather: str = "맑음"           # 맑음 | 비 | 눈
    walk_limit: int = 10            # 우천 시 도보 제한(분)
    people: int | None = None       # 회식 인원
    max_price: int | None = None    # 회식 예산(1~3)
    max_spice: int | None = None    # 메뉴 모드 맵기 제한
    keyword: str = ""               # 검색어(A9)
    cooldown_days: int = 3


@dataclass
class Candidate:
    name: str
    category: str
    weight: float = 1.0
    item: Restaurant | MenuItem | None = None

    @property
    def display(self) -> str:
        return self.item.display if self.item else self.name


def _recent_choices(store: DataStore, days: int, menu_mode: bool) -> set[str]:
    """최근 N일 선택. 메뉴 이력과 식당 이력은 분리해 매칭한다.

    '김치찌개(메뉴)'를 골랐다고 '김치찌개집(식당)'이 감점되지 않도록.
    """
    if days <= 0:
        return set()
    cutoff = (date.today() - timedelta(days=days)).isoformat()
    return {h.choice for h in store.history
            if h.date >= cutoff and (h.mode == MODE_MENU) == menu_mode}


def _match_keyword(kw: str, name: str, category: str, tags: list[str]) -> bool:
    kw = kw.strip().lower()
    if not kw:
        return True
    hay = " ".join([name, category, *tags]).lower()
    return kw in hay


def collect_candidates(store: DataStore, q: Query) -> list[Candidate]:
    """필터를 통과한 후보 목록(가중치 포함). 0개일 수 있다 — UI가 안내."""
    excluded = set(store.excluded)
    favorites = set(store.favorites)
    recent = _recent_choices(store, q.cooldown_days, menu_mode=(q.mode == MODE_MENU))
    out: list[Candidate] = []

    if q.mode == MODE_MENU:
        for m in store.menus:
            if m.name in excluded:
                continue
            if q.categories and m.category not in q.categories:
                continue
            if q.max_spice is not None and m.spice > q.max_spice:
                continue
            if not _match_keyword(q.keyword, m.name, m.category, []):
                continue
            out.append(Candidate(m.name, m.category, item=m))
    else:
        rainy = q.weather in ("비", "눈")
        for r in store.all_restaurants():
            if r.name in excluded:
                continue
            if q.categories and r.category not in q.categories:
                continue
            if rainy and not (r.rain_ok or r.walk_min <= q.walk_limit):
                continue
            if q.mode == MODE_DINING:
                if q.people and r.capacity < q.people:
                    continue
                if q.max_price and r.price > q.max_price:
                    continue
            if not _match_keyword(q.keyword, r.name, r.category, r.tags):
                continue
            c = Candidate(r.name, r.category, item=r)
            if rainy and r.rain_ok:
                c.weight *= 1.3  # 우천 시 비올때OK 가중(기획안 F3)
            out.append(c)

    for c in out:
        if c.name in recent:
            c.weight *= COOLDOWN_PENALTY  # A1: 제외 대신 감점 → 후보 고갈 방지
        if c.name in favorites:
            c.weight *= FAVORITE_BOOST
    return out


def collect_with_relaxation(store: DataStore, q: Query) -> tuple[list[Candidate], list[str]]:
    """후보 0개면 조건을 단계적으로 완화하고, 적용한 완화 내용을 함께 반환.

    완화 순서: 도보 제한 2배 → 날씨 필터 해제 → 카테고리 필터 해제.
    그래도 0개면 (빈 목록, 완화 내역)을 돌려주고 UI가 빈 상태 화면을 띄운다.
    """
    notes: list[str] = []
    cands = collect_candidates(store, q)
    if not cands and q.weather in ("비", "눈"):
        q = replace(q, walk_limit=q.walk_limit * 2)
        cands = collect_candidates(store, q)
        if cands:
            notes.append(f"도보 제한을 {q.walk_limit}분으로 완화했어요")
    if not cands and q.weather in ("비", "눈"):
        q = replace(q, weather="맑음")
        cands = collect_candidates(store, q)
        if cands:
            notes.append("날씨 필터를 해제했어요")
    if not cands and q.categories:
        q = replace(q, categories=set())
        cands = collect_candidates(store, q)
        if cands:
            notes.append("카테고리 필터를 해제했어요")
    return cands, notes


def weighted_pick(candidates: list[Candidate], rng: random.Random | None = None) -> Candidate | None:
    if not candidates:
        return None
    rng = rng or random
    return rng.choices(candidates, weights=[max(c.weight, 0.001) for c in candidates], k=1)[0]


def pick_slots(candidates: list[Candidate], n: int = 8, rng: random.Random | None = None) -> list[Candidate]:
    """룰렛 칸/투표 후보용 — 가중치 기반 비복원 추출 최대 n개."""
    rng = rng or random
    pool = list(candidates)
    slots: list[Candidate] = []
    while pool and len(slots) < n:
        pick = weighted_pick(pool, rng)
        slots.append(pick)
        pool.remove(pick)
    rng.shuffle(slots)
    return slots
