"""이력/통계 (A4) — 벤토 통계 타일(카운트업) + TOP5 바 + 최근 기록 (기획안 v2 5.4)."""
from __future__ import annotations

import customtkinter as ctk

from .. import stats
from ..recommender import MODE_DINING, MODE_DINNER, MODE_LUNCH
from . import theme, widgets


class HistoryTab(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self._build()

    def _build(self) -> None:
        tiles = ctk.CTkFrame(self, fg_color="transparent")
        tiles.pack(fill="x", pady=(0, 10))
        self._tiles: dict[str, ctk.CTkLabel] = {}
        for i, name in enumerate(("이번 달", MODE_LUNCH, MODE_DINNER, MODE_DINING)):
            tiles.grid_columnconfigure(i, weight=1)
            card = widgets.Card(tiles)
            card.grid(row=0, column=i, sticky="ew", padx=(0 if i == 0 else 8, 0))
            ctk.CTkLabel(card, text=name, font=theme.font(11),
                         text_color=theme.TEXT_DIM).pack(pady=(12, 0))
            value = ctk.CTkLabel(card, text="0회", font=theme.font(20, bold=True),
                                 text_color=theme.TOMATO_HOVER if i == 0 else theme.TEXT_HI)
            value.pack(pady=(0, 12))
            self._tiles[name] = value

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True)
        body.grid_columnconfigure((0, 1), weight=1)
        body.grid_rowconfigure(0, weight=1)

        top_card = widgets.Card(body, title="이번 달 TOP 5", hoverable=False)
        top_card.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        self.top_list = widgets.ListPanel(top_card, height=260)
        self.top_list.pack(fill="both", expand=True, padx=10, pady=(0, 12))

        recent_card = widgets.Card(body, title="최근 기록 20건", hoverable=False)
        recent_card.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        self.recent_list = widgets.ListPanel(recent_card, height=260)
        self.recent_list.pack(fill="both", expand=True, padx=10, pady=(0, 12))

    def refresh(self) -> None:
        history = self.app.store.history
        month = stats.month_entries(history)
        modes = stats.mode_breakdown(month)
        widgets.count_up(self._tiles["이번 달"], len(month))
        for mode in (MODE_LUNCH, MODE_DINNER, MODE_DINING):
            widgets.count_up(self._tiles[mode], modes.get(mode, 0))

        self.top_list.clear()
        top = stats.top_choices(month, 5)
        max_count = top[0][1] if top else 1
        for i, (name, cnt) in enumerate(top, 1):
            medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, f"{i}.")
            self.top_list.add_row(f"{medal} {name}", sub=f"{cnt}회",
                                  bar_ratio=cnt / max_count)
        if not month:
            self.top_list.add_row("아직 기록이 없어요")

        self.recent_list.clear()
        for h in list(reversed(history))[:20]:
            self.recent_list.add_row(f"{h.date}  [{h.mode}]  {h.choice}")
