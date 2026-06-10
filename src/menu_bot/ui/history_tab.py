"""이력/통계 탭 (A4): 이번 달 사용량, TOP5, 최근 기록."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from .. import stats
from . import theme


class HistoryTab(ttk.Frame):
    def __init__(self, master, app):
        super().__init__(master)
        self.app = app
        self._build()

    def _build(self) -> None:
        top = ttk.Frame(self)
        top.pack(fill="x", padx=10, pady=6)
        ttk.Button(top, text="🔄 새로고침", command=self.refresh).pack(side="left")
        self.summary = tk.Label(top, text="", font=theme.FONT_BOLD, fg=theme.NORI)
        self.summary.pack(side="left", padx=10)

        body = ttk.Frame(self)
        body.pack(fill="both", expand=True, padx=10, pady=4)

        left = ttk.LabelFrame(body, text="이번 달 TOP 5")
        left.pack(side="left", fill="both", expand=True, padx=(0, 5))
        self.top_list = tk.Listbox(left, font=theme.FONT, height=8)
        self.top_list.pack(fill="both", expand=True, padx=4, pady=4)

        right = ttk.LabelFrame(body, text="최근 기록 20건")
        right.pack(side="left", fill="both", expand=True, padx=(5, 0))
        self.recent_list = tk.Listbox(right, font=theme.FONT, height=8)
        self.recent_list.pack(fill="both", expand=True, padx=4, pady=4)

    def refresh(self) -> None:
        history = self.app.store.history
        month = stats.month_entries(history)
        modes = stats.mode_breakdown(month)
        mode_text = " · ".join(f"{m} {c}회" for m, c in modes.items()) or "기록 없음"
        self.summary.configure(text=f"이번 달 {len(month)}회 — {mode_text}")

        self.top_list.delete(0, "end")
        for i, (name, cnt) in enumerate(stats.top_choices(month, 5), 1):
            medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, f"{i}.")
            self.top_list.insert("end", f"{medal} {name} — {cnt}회")
        if not month:
            self.top_list.insert("end", "아직 기록이 없어요")

        self.recent_list.delete(0, "end")
        for h in list(reversed(history))[:20]:
            self.recent_list.insert("end", f"{h.date}  [{h.mode}]  {h.choice}")
