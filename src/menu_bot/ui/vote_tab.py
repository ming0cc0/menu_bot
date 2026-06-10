"""그룹 투표 탭 (A3): 후보 3~5개 → 다수결 + 거부권."""
from __future__ import annotations

import random
import tkinter as tk
from tkinter import ttk

from .. import recommender as rec
from ..recommender import MODE_DINING, MODE_DINNER, MODE_LUNCH
from . import theme


class VoteTab(ttk.Frame):
    def __init__(self, master, app):
        super().__init__(master)
        self.app = app
        self.mode = tk.StringVar(value=MODE_LUNCH)
        self.count = tk.IntVar(value=5)
        self.rows: list[dict] = []
        self._build()

    def _build(self) -> None:
        top = ttk.Frame(self)
        top.pack(fill="x", padx=10, pady=8)
        ttk.Label(top, text="모드:").pack(side="left")
        for m in (MODE_LUNCH, MODE_DINNER, MODE_DINING):
            ttk.Radiobutton(top, text=m, value=m, variable=self.mode).pack(side="left", padx=4)
        ttk.Label(top, text="  후보 수:").pack(side="left")
        ttk.Spinbox(top, from_=3, to=5, width=3, textvariable=self.count).pack(side="left")
        ttk.Button(top, text="후보 뽑기", command=self.draw).pack(side="left", padx=8)

        self.board = ttk.Frame(self)
        self.board.pack(fill="both", expand=True, padx=10)

        bottom = ttk.Frame(self)
        bottom.pack(fill="x", padx=10, pady=8)
        self.decide_btn = ttk.Button(bottom, text="🏆 결정!", command=self.decide,
                                     state="disabled")
        self.decide_btn.pack(side="left")
        self.result = tk.Label(bottom, text="", font=theme.FONT_TITLE,
                               fg=theme.TOMATO_SHADOW)
        self.result.pack(side="left", padx=10)

    def draw(self) -> None:
        q = rec.Query(mode=self.mode.get(),
                      cooldown_days=self.app.cfg.cooldown_days)
        cands, _ = rec.collect_with_relaxation(self.app.store, q)
        slots = rec.pick_slots(cands, self.count.get())
        for w in self.board.winfo_children():
            w.destroy()
        self.rows = []
        self.result.configure(text="")
        if not slots:
            ttk.Label(self.board, text="후보가 없어요 — 데이터를 확인하세요").pack(pady=20)
            self.decide_btn.configure(state="disabled")
            return
        for c in slots:
            row = ttk.Frame(self.board)
            row.pack(fill="x", pady=3)
            votes = tk.IntVar(value=0)
            vetoed = tk.BooleanVar(value=False)
            label = ttk.Label(row, text=c.display, width=36, font=theme.FONT_BOLD)
            label.pack(side="left")
            count_lbl = ttk.Label(row, text="0표", width=5)
            count_lbl.pack(side="left")

            def plus(v=votes, lbl=count_lbl):
                v.set(v.get() + 1)
                lbl.configure(text=f"{v.get()}표")

            ttk.Button(row, text="+1", width=4, command=plus).pack(side="left", padx=2)
            ttk.Checkbutton(row, text="거부권", variable=vetoed).pack(side="left", padx=6)
            self.rows.append({"cand": c, "votes": votes, "veto": vetoed})
        self.decide_btn.configure(state="normal")

    def decide(self) -> None:
        alive = [r for r in self.rows if not r["veto"].get()]
        if not alive:
            self.result.configure(text="전부 거부됐어요 😅 다시 뽑아요!")
            return
        top = max(r["votes"].get() for r in alive)
        winners = [r for r in alive if r["votes"].get() == top]
        chosen = random.choice(winners)["cand"]  # 동률은 랜덤
        self.app.store.record_history(self.mode.get(), chosen.name)
        suffix = " (동률 추첨)" if len(winners) > 1 else ""
        self.result.configure(text=f"🏆 {chosen.display}{suffix} — 기록했어요!")
        self.decide_btn.configure(state="disabled")
