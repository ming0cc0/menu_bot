"""그룹 투표 (A3) — 후보 카드 + 득표 비례 바 + 거부권 (기획안 v2 5.2)."""
from __future__ import annotations

import random
import tkinter as tk

import customtkinter as ctk

from .. import recommender as rec
from ..recommender import MODE_DINING, MODE_DINNER, MODE_LUNCH
from . import theme, widgets


class VoteTab(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.mode = tk.StringVar(value=MODE_LUNCH)
        self.count = tk.IntVar(value=5)
        self.rows: list[dict] = []
        self._strike = ctk.CTkFont(family=theme.FONT_FAMILY, size=12,
                                   overstrike=True)
        self._build()

    def _build(self) -> None:
        top = widgets.Card(self, title="투표 설정", hoverable=False)
        top.pack(fill="x", pady=(0, 10))
        row = ctk.CTkFrame(top, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=(2, 14))
        self.mode_seg = ctk.CTkSegmentedButton(
            row, values=[MODE_LUNCH, MODE_DINNER, MODE_DINING],
            font=theme.font(11), selected_color=theme.TOMATO,
            selected_hover_color=theme.TOMATO_HOVER,
            unselected_color=theme.BG_ELEV, unselected_hover_color=theme.BG_HOVER,
            fg_color=theme.BG_ELEV, text_color=theme.TEXT_HI,
            command=lambda v: self.mode.set(v))
        self.mode_seg.set(MODE_LUNCH)
        self.mode_seg.pack(side="left")
        ctk.CTkLabel(row, text="후보 수", font=theme.font(11),
                     text_color=theme.TEXT_MID).pack(side="left", padx=(16, 6))
        widgets.Stepper(row, self.count, 3, 5).pack(side="left")
        ctk.CTkButton(row, text="후보 뽑기", font=theme.font(11, bold=True),
                      corner_radius=16, height=32, fg_color=theme.BG_ELEV,
                      hover_color=theme.BG_HOVER, text_color=theme.TEXT_HI,
                      command=self.draw).pack(side="right")

        self.board = ctk.CTkFrame(self, fg_color="transparent")
        self.board.pack(fill="both", expand=True)

        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.pack(fill="x", pady=10)
        self.decide_btn = ctk.CTkButton(
            bottom, text="🏆 결정!", font=theme.font(13, bold=True),
            corner_radius=20, height=40, width=130, fg_color=theme.TOMATO,
            hover_color=theme.TOMATO_HOVER, text_color="#FFFFFF",
            state="disabled", command=self.decide)
        self.decide_btn.pack(side="left")
        self.result = ctk.CTkLabel(bottom, text="", font=theme.font(13, bold=True),
                                   text_color=theme.TOMATO_HOVER)
        self.result.pack(side="left", padx=14)

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
            empty = widgets.Card(self.board, hoverable=False)
            empty.pack(fill="x", pady=20)
            ctk.CTkLabel(empty, text="후보가 없어요 — 데이터를 확인하세요",
                         font=theme.font(12), text_color=theme.TEXT_DIM).pack(pady=20)
            self.decide_btn.configure(state="disabled")
            return
        for c in slots:
            card = widgets.Card(self.board)
            card.pack(fill="x", pady=4)
            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="x", padx=16, pady=10)
            votes = tk.IntVar(value=0)
            vetoed = tk.BooleanVar(value=False)
            name_lbl = ctk.CTkLabel(inner, text=c.display, font=theme.font(12, bold=True),
                                    text_color=theme.TEXT_HI, anchor="w", width=280)
            name_lbl.pack(side="left")
            bar = ctk.CTkProgressBar(inner, width=140, height=8,
                                     progress_color=theme.TOMATO,
                                     fg_color=theme.BG_ELEV)
            bar.set(0)
            bar.pack(side="left", padx=10)
            count_lbl = ctk.CTkLabel(inner, text="0표", font=theme.font(11),
                                     text_color=theme.TEXT_MID, width=40)
            count_lbl.pack(side="left")
            entry = {"cand": c, "votes": votes, "veto": vetoed, "bar": bar,
                     "count_lbl": count_lbl, "name_lbl": name_lbl, "card": card}

            def plus(e=entry):
                e["votes"].set(e["votes"].get() + 1)
                e["count_lbl"].configure(text=f"{e['votes'].get()}표")
                self._update_bars()

            def veto(e=entry):
                on = not e["veto"].get()
                e["veto"].set(on)
                # 색+형태 이중 신호: 회색 처리 + 취소선
                e["name_lbl"].configure(
                    text_color=theme.TEXT_DIM if on else theme.TEXT_HI,
                    font=self._strike if on else theme.font(12, bold=True))
                e["card"].configure(fg_color=theme.BG_BASE if on else theme.BG_CARD)

            ctk.CTkButton(inner, text="+1", width=40, height=28, corner_radius=14,
                          font=theme.font(11, bold=True), fg_color=theme.BG_ELEV,
                          hover_color=theme.BG_HOVER, text_color=theme.TEXT_HI,
                          command=plus).pack(side="left", padx=4)
            ctk.CTkButton(inner, text="거부 ✕", width=60, height=28, corner_radius=14,
                          font=theme.font(11), fg_color="transparent",
                          border_width=1, border_color=theme.BORDER,
                          hover_color=theme.BG_HOVER, text_color=theme.TEXT_DIM,
                          command=veto).pack(side="left", padx=4)
            self.rows.append(entry)
        self.decide_btn.configure(state="normal")

    def _update_bars(self) -> None:
        top = max((r["votes"].get() for r in self.rows), default=0)
        for r in self.rows:
            r["bar"].set(r["votes"].get() / top if top else 0)

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
