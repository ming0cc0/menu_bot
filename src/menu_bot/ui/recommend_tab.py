"""추천 홈 — 벤토 그리드: 조건 카드 + 히어로 룰렛 + 결과 카드 (기획안 v2 5.1)."""
from __future__ import annotations

import random
import tkinter as tk
from datetime import datetime

import customtkinter as ctk

from .. import recommender as rec
from ..recommender import MODE_DINING, MODE_DINNER, MODE_LUNCH, MODE_MENU, Query
from . import theme, widgets
from .roulette import RouletteCanvas

MAX_SLOTS = 8  # 후보 과다 시 가중 선샘플링 (기획안 12.3)

MODES = [MODE_LUNCH, MODE_DINNER, MODE_DINING, MODE_MENU]
WEATHER_LABELS = {"☀ 맑음": "맑음", "🌧 비": "비", "❄ 눈": "눈"}
BUDGET_LABELS = ["예산 전체", "1 (~1만원)", "2 (1~2만원)", "3 (2만원~)"]


def _greeting() -> str:
    now = datetime.now()
    hhmm = now.strftime("%H:%M")
    h = now.hour
    if h < 10:
        msg = "굿모닝! 오늘 점심, 미리 정해둘까요? ☀️"
    elif h < 13:
        msg = "슬슬 배고프죠? 🍙"
    elif h < 16:
        msg = "오후엔 커피… 저녁은 밥봇이 골라드려요 ☕"
    elif h < 19:
        msg = "저녁 뭐 먹지? 🍜"
    else:
        msg = "야근엔 든든한 한 끼! 💪"
    return f"{hhmm} — {msg}"


class RecommendTab(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app  # MenuBotApp: .store, .cfg
        self.mode = tk.StringVar(value=MODE_LUNCH)
        self.keyword = tk.StringVar()
        self.people = tk.IntVar(value=8)
        self.cat_vars: dict[str, tk.BooleanVar] = {}
        self.candidates: list[rec.Candidate] = []
        self.slots: list[rec.Candidate] = []
        self.winner: rec.Candidate | None = None
        self.notes: list[str] = []
        self._build()
        self.refresh_weather_from_file()

    # ---------------------------------------------------------- 레이아웃
    def _build(self) -> None:
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # 헤더: 시간대 인사 + 날씨 세그먼트
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        self.greeting = ctk.CTkLabel(header, text=_greeting(),
                                     font=theme.font(15, bold=True),
                                     text_color=theme.TEXT_HI)
        self.greeting.pack(side="left")
        self.weather_seg = ctk.CTkSegmentedButton(
            header, values=list(WEATHER_LABELS), font=theme.font(11),
            selected_color=theme.TOMATO, selected_hover_color=theme.TOMATO_HOVER,
            unselected_color=theme.BG_ELEV, unselected_hover_color=theme.BG_HOVER,
            fg_color=theme.BG_ELEV, text_color=theme.TEXT_HI)
        self.weather_seg.set("☀ 맑음")
        self.weather_seg.pack(side="right")

        # ---- 좌열: 조건 벤토 ----
        left = ctk.CTkFrame(self, fg_color="transparent", width=320)
        left.grid(row=1, column=0, sticky="nsw", padx=(0, 12))
        left.grid_propagate(False)

        mode_card = widgets.Card(left, title="모드")
        mode_card.pack(fill="x", pady=(0, 8))
        self.mode_seg = ctk.CTkSegmentedButton(
            mode_card, values=MODES, font=theme.font(11),
            selected_color=theme.TOMATO, selected_hover_color=theme.TOMATO_HOVER,
            unselected_color=theme.BG_ELEV, unselected_hover_color=theme.BG_HOVER,
            fg_color=theme.BG_ELEV, text_color=theme.TEXT_HI,
            command=self._on_mode_change)
        self.mode_seg.set(MODE_LUNCH)
        self.mode_seg.pack(fill="x", padx=16, pady=(4, 14))

        self.cat_card = widgets.Card(left, title="카테고리 — 없으면 전체")
        self.cat_card.pack(fill="x", pady=8)
        self.cat_chip_area = ctk.CTkFrame(self.cat_card, fg_color="transparent")
        self.cat_chip_area.pack(fill="x", padx=12, pady=(2, 12))
        self._rebuild_categories()

        # 회식 조건 (모드=회식일 때만)
        self.dining_card = widgets.Card(left, title="회식 조건")
        row = ctk.CTkFrame(self.dining_card, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=(2, 12))
        ctk.CTkLabel(row, text="인원", font=theme.font(11),
                     text_color=theme.TEXT_MID).pack(side="left")
        widgets.Stepper(row, self.people, 2, 50).pack(side="left", padx=8)
        self.budget_menu = ctk.CTkOptionMenu(
            row, values=BUDGET_LABELS, font=theme.font(11), width=120,
            fg_color=theme.BG_ELEV, button_color=theme.BG_HOVER,
            button_hover_color=theme.TOMATO_PRESS, text_color=theme.TEXT_HI,
            dropdown_fg_color=theme.BG_ELEV, dropdown_hover_color=theme.BG_HOVER,
            dropdown_text_color=theme.TEXT_HI)
        self.budget_menu.pack(side="right")

        search_card = widgets.Card(left, title="검색")
        search_card.pack(fill="x", pady=8)
        ctk.CTkEntry(search_card, textvariable=self.keyword,
                     placeholder_text="식당·메뉴·태그 키워드",
                     font=theme.font(11), fg_color=theme.BG_ELEV,
                     border_color=theme.BORDER, text_color=theme.TEXT_HI).pack(
            fill="x", padx=16, pady=(2, 14))

        self.spin_btn = ctk.CTkButton(
            left, text="▶  룰렛 돌리기!", height=52, corner_radius=26,
            font=theme.font(17, bold=True), fg_color=theme.TOMATO,
            hover_color=theme.TOMATO_HOVER, text_color="#FFFFFF",
            command=self.spin)
        self.spin_btn.pack(fill="x", pady=(12, 0))

        # ---- 우열: 룰렛 카드 + 결과 카드 ----
        right = ctk.CTkFrame(self, fg_color="transparent")
        right.grid(row=1, column=1, sticky="nsew")

        wheel_card = widgets.Card(right, hoverable=False)
        wheel_card.pack(fill="both", expand=True)
        status_row = ctk.CTkFrame(wheel_card, fg_color="transparent")
        status_row.pack(fill="x", padx=16, pady=(12, 0))
        self.status_mascot = ctk.CTkLabel(status_row, text="",
                                          image=theme.mascot("base", 44))
        self.status_mascot.pack(side="left")
        self.status = ctk.CTkLabel(status_row, text="오늘 뭐 먹지? 버튼을 눌러요!",
                                   font=theme.font(12, bold=True),
                                   text_color=theme.TEXT_MID, justify="left",
                                   wraplength=250, anchor="w")
        self.status.pack(side="left", padx=10, fill="x", expand=True)
        self.wheel = RouletteCanvas(wheel_card, size=310)
        self.wheel.pack(pady=(2, 10))

        self.result_card = widgets.Card(right, hoverable=False,
                                        border_color=theme.BORDER_GLOW)
        result_top = ctk.CTkFrame(self.result_card, fg_color="transparent")
        result_top.pack(fill="x", padx=16, pady=(12, 0))
        self.result_mascot = ctk.CTkLabel(result_top, text="",
                                          image=theme.mascot("happy", 56))
        self.result_mascot.pack(side="left")
        body = ctk.CTkFrame(result_top, fg_color="transparent")
        body.pack(side="left", fill="x", expand=True, padx=12)
        self.result_text = ctk.CTkLabel(body, text="", font=theme.font(18, bold=True),
                                        text_color=theme.TEXT_HI, anchor="w",
                                        justify="left", wraplength=240)
        self.result_text.pack(fill="x")
        self.result_sub = ctk.CTkLabel(body, text="", font=theme.font(11),
                                       text_color=theme.TEXT_MID, anchor="w",
                                       justify="left", wraplength=240)
        self.result_sub.pack(fill="x")
        btn_kw = dict(height=32, corner_radius=16, font=theme.font(11),
                      fg_color=theme.BG_ELEV, hover_color=theme.BG_HOVER,
                      text_color=theme.TEXT_HI)
        row1 = ctk.CTkFrame(self.result_card, fg_color="transparent")
        row1.pack(fill="x", padx=14, pady=(8, 2))
        self.accept_btn = ctk.CTkButton(row1, text="✅ 이걸로 결정", command=self.accept,
                                        height=32, corner_radius=16,
                                        font=theme.font(11, bold=True),
                                        fg_color=theme.TOMATO,
                                        hover_color=theme.TOMATO_HOVER,
                                        text_color="#FFFFFF", width=120)
        self.accept_btn.pack(side="left", padx=3)
        ctk.CTkButton(row1, text="🔄 다시", command=self.spin, width=70,
                      **btn_kw).pack(side="left", padx=3)
        ctk.CTkButton(row1, text="📋 복사", command=self.copy_result, width=70,
                      **btn_kw).pack(side="left", padx=3)
        row2 = ctk.CTkFrame(self.result_card, fg_color="transparent")
        row2.pack(fill="x", padx=14, pady=(2, 12))
        self.fav_btn = ctk.CTkButton(row2, text="⭐ 즐겨찾기", command=self.toggle_favorite,
                                     width=100, **btn_kw)
        self.fav_btn.pack(side="left", padx=3)
        ctk.CTkButton(row2, text="🚫 제외", command=self.exclude_winner, width=70,
                      **btn_kw).pack(side="left", padx=3)

        self._on_mode_change(MODE_LUNCH)
        self._tick_greeting()

    def _tick_greeting(self) -> None:
        if not self.winfo_exists():
            return
        self.greeting.configure(text=_greeting())
        self.after(60_000, self._tick_greeting)

    def _set_mascot(self, expr: str) -> None:
        self.status_mascot.configure(image=theme.mascot(expr, 44))

    def _rebuild_categories(self) -> None:
        for w in self.cat_chip_area.winfo_children():
            w.destroy()
        selected = {c for c, v in self.cat_vars.items() if v.get()}
        if self.mode.get() == MODE_MENU:
            cats = sorted({m.category for m in self.app.store.menus})
        else:
            cats = sorted({r.category for r in self.app.store.all_restaurants()})
        self.cat_vars = {}
        row = ctk.CTkFrame(self.cat_chip_area, fg_color="transparent")
        row.pack(anchor="w")
        for i, cat in enumerate(cats):
            if i and i % 3 == 0:
                row = ctk.CTkFrame(self.cat_chip_area, fg_color="transparent")
                row.pack(anchor="w", pady=(4, 0))
            var = tk.BooleanVar(value=cat in selected)
            self.cat_vars[cat] = var
            widgets.Chip(row, cat, var).pack(side="left", padx=3)

    def _on_mode_change(self, value: str) -> None:
        self.mode.set(value)
        if value == MODE_DINING:
            self.dining_card.pack(fill="x", pady=8, after=self.cat_card)
        else:
            self.dining_card.pack_forget()
        self._rebuild_categories()

    def refresh_weather_from_file(self) -> None:
        """weather.txt 값(오늘자만 유효)을 초기 토글값으로. 수동 변경이 우선."""
        w = self.app.store.weather_file
        if w:
            for label, value in WEATHER_LABELS.items():
                if value == w:
                    self.weather_seg.set(label)

    # ---------------------------------------------------------- 추첨
    def build_query(self) -> Query:
        cats = {c for c, v in self.cat_vars.items() if v.get()}
        budget = BUDGET_LABELS.index(self.budget_menu.get())  # 0=전체
        return Query(
            mode=self.mode.get(), categories=cats,
            weather=WEATHER_LABELS.get(self.weather_seg.get(), "맑음"),
            walk_limit=self.app.cfg.default_walk_limit,
            people=self.people.get() if self.mode.get() == MODE_DINING else None,
            max_price=budget if (self.mode.get() == MODE_DINING and budget) else None,
            keyword=self.keyword.get(), cooldown_days=self.app.cfg.cooldown_days)

    def spin(self) -> None:
        if self.wheel.spinning:
            return
        self.wheel.stop()
        self._rebuild_categories()
        self.candidates, self.notes = rec.collect_with_relaxation(
            self.app.store, self.build_query())
        self.result_card.pack_forget()
        if not self.candidates:
            # 빈 상태: 배고픈 마스코트가 데이터 추가를 안내 (기획안 v2 5.1)
            self._set_mascot("hungry")
            self.status.configure(text="조건에 맞는 후보가 없어요.\n"
                                       "필터를 풀거나 메뉴를 추가해 주세요!")
            self.wheel.set_candidates([])
            return
        self.winner = rec.weighted_pick(self.candidates)
        self.slots = rec.pick_slots(self.candidates, MAX_SLOTS)
        if self.winner.name in {s.name for s in self.slots}:
            idx = next(i for i, s in enumerate(self.slots)
                       if s.name == self.winner.name)
        else:
            # 동명 후보가 있어도 안전하도록 교체한 칸 인덱스를 그대로 사용
            idx = random.randrange(len(self.slots))
            self.slots[idx] = self.winner
        info = f"후보 {len(self.candidates)}개"
        if len(self.candidates) > len(self.slots):
            info += f" 중 {len(self.slots)}개 표시"
        self.status.configure(text=f"고민중… ({info})")
        self._set_mascot("dizzy")
        self.wheel.set_candidates([s.name for s in self.slots])
        self.wheel.spin_to(idx, self._on_spin_done)

    def _on_spin_done(self) -> None:
        self._set_mascot("happy")
        w = self.winner
        self.status.configure(text="당첨! 🎉")
        detail = []
        if w.item is not None and hasattr(w.item, "walk_min"):
            r = w.item
            detail.append(f"도보 {r.walk_min}분 · 가격대 {r.price} · ~{r.capacity}명")
            if r.tags:
                detail.append("태그: " + ", ".join(r.tags))
        for note in self.notes:
            detail.append("ℹ️ " + note)
        self.result_text.configure(text=w.display)
        self.result_sub.configure(text="\n".join(detail))
        self._update_fav_btn()
        self.accept_btn.configure(state="normal")
        # 결과 카드 슬라이드 인 (250ms)
        self.result_card.pack(fill="x", pady=(28, 0))
        widgets.animate(self.result_card, 10, 250,
                        lambda t: self.result_card.pack_configure(
                            pady=(round(28 - 18 * t), 0)))

    # ---------------------------------------------------------- 결과 액션
    def accept(self) -> None:
        if not self.winner:
            return
        ok = self.app.store.record_history(self.mode.get(), self.winner.name)
        self.accept_btn.configure(state="disabled")
        self.status.configure(text="기록했어요! 맛있게 드세요 🍙" if ok
                              else "기록 실패 — error.log를 확인하세요")

    def copy_result(self) -> None:
        if not self.winner:
            return
        text = f"오늘 {self.mode.get()}: {self.winner.display}"
        self.clipboard_clear()
        self.clipboard_append(text)
        self.status.configure(text="클립보드에 복사했어요 📋")

    def toggle_favorite(self) -> None:
        if not self.winner:
            return
        on = self.winner.name not in self.app.store.favorites
        self.app.store.set_favorite(self.winner.name, on)
        self._update_fav_btn()

    def _update_fav_btn(self) -> None:
        if self.winner and self.winner.name in self.app.store.favorites:
            self.fav_btn.configure(text="⭐ 해제", text_color=theme.WARN)
        else:
            self.fav_btn.configure(text="⭐ 즐겨찾기", text_color=theme.TEXT_HI)

    def exclude_winner(self) -> None:
        if not self.winner:
            return
        self.app.store.set_excluded(self.winner.name, True)
        self.status.configure(text=f"'{self.winner.name}' 제외 목록에 추가 "
                                   "(설정에서 해제 가능)")
