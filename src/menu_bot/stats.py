"""history.txt 기반 이력/통계 (A4, KPI)."""
from __future__ import annotations

from collections import Counter
from datetime import date

from .models import HistoryEntry


def month_entries(history: list[HistoryEntry], year: int | None = None,
                  month: int | None = None) -> list[HistoryEntry]:
    today = date.today()
    prefix = f"{year or today.year:04d}-{month or today.month:02d}-"
    return [h for h in history if h.date.startswith(prefix)]


def top_choices(history: list[HistoryEntry], n: int = 5) -> list[tuple[str, int]]:
    return Counter(h.choice for h in history).most_common(n)


def usage_by_day(history: list[HistoryEntry]) -> dict[str, int]:
    counter = Counter(h.date for h in history)
    return dict(sorted(counter.items()))


def mode_breakdown(history: list[HistoryEntry]) -> dict[str, int]:
    return dict(Counter(h.mode for h in history))
