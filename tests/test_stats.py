from __future__ import annotations

from datetime import date

from menu_bot.models import HistoryEntry
from menu_bot.stats import mode_breakdown, month_entries, top_choices, usage_by_day


def entry(d: str, mode: str = "점심", choice: str = "가까운한식") -> HistoryEntry:
    return HistoryEntry(date=d, mode=mode, choice=choice)


def test_month_entries():
    today = date.today()
    this_month = f"{today.year:04d}-{today.month:02d}-05"
    hist = [entry(this_month), entry("2000-01-01")]
    assert len(month_entries(hist)) == 1
    assert len(month_entries(hist, 2000, 1)) == 1


def test_top_choices():
    hist = [entry("2026-06-01"), entry("2026-06-02"),
            entry("2026-06-03", choice="먼일식")]
    top = top_choices(hist, n=2)
    assert top[0] == ("가까운한식", 2)


def test_usage_and_modes():
    hist = [entry("2026-06-01"), entry("2026-06-01", mode="회식"), entry("2026-06-02")]
    assert usage_by_day(hist) == {"2026-06-01": 2, "2026-06-02": 1}
    assert mode_breakdown(hist) == {"점심": 2, "회식": 1}
