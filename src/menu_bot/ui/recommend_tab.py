"""메인 추천 탭: 모드/날씨/필터 → 룰렛 → 결과 카드."""
from __future__ import annotations

import random
import tkinter as tk
from tkinter import ttk

from .. import recommender as rec
from ..recommender import MODE_DINING, MODE_DINNER, MODE_LUNCH, MODE_MENU, Query
from . import theme
from .roulette import RouletteCanvas

MAX_SLOTS = 8  # 룰렛 칸 수 상한 — 초과분은 가중 선샘플링 (UX 보완)

PRICE_LABELS = {0: "전체", 1: "1 (~1만원)", 2: "2 (1~2만원)", 3: "3 (2만원~)"}
WEATHERS = [("☀️ 맑음", "맑음"), ("🌧️ 비", "비"), ("❄️ 눈", "눈")]


class RecommendTab(ttk.Frame):
    def __init__(self, master, app):
        super().__init__(master)
        self.app = app  # MenuBotApp: .store, .cfg
        self.mode = tk.StringVar(value=MODE_LUNCH)
        self.weather = tk.StringVar(value="맑음")
        self.keyword = tk.StringVar()
        self.people = tk.IntVar(value=8)
        self.budget = tk.IntVar(value=0)
        self.cat_vars: dict[str, tk.BooleanVar] = {}
        self.candidates: list[rec.Candidate] = []
        self.slots: list[rec.Candidate] = []
        self.winner: rec.Candidate | None = None
        self.notes: list[str] = []
        self._build()
        self.refresh_weather_from_file()

    # ---------------------------------------------------------- 레이아웃
    def _build(self) -> None:
        left = ttk.Frame(self)
        left.pack(side="left", fill="y", padx=(10, 6), pady=8)
        right = ttk.Frame(self)
        right.pack(side="left", fill="both", expand=True, padx=(6, 10), pady=8)

        # 모드
        box = ttk.LabelFrame(left, text="모드")
        box.pack(fill="x", pady=(0, 6))
        for m in (MODE_LUNCH, MODE_DINNER, MODE_DINING, MODE_MENU):
            label = m if m != MODE_MENU else "메뉴만(식당 무관)"
            ttk.Radiobutton(box, text=label, value=m, variable=self.mode,
                            command=self._on_mode_change).pack(anchor="w", padx=8, pady=1)

        # 날씨 (수동 토글이 weather.txt보다 우선)
        box = ttk.LabelFrame(left, text="날씨")
        box.pack(fill="x", pady=6)
        for text, value in WEATHERS:
            ttk.Radiobutton(box, text=text, value=value,
                            variable=self.weather).pack(anchor="w", padx=8, pady=1)

        # 카테고리 칩
        self.cat_box = ttk.LabelFrame(left, text="카테고리 (없으면 전체)")
        self.cat_box.pack(fill="x", pady=6)
        self._rebuild_categories()

        # 회식 조건
        self.dining_box = ttk.LabelFrame(left, text="회식 조건")
        ttk.Label(self.dining_box, text="인원").grid(row=0, column=0, padx=6, pady=3)
        ttk.Spinbox(self.dining_box, from_=2, to=50, width=5,
                    textvariable=self.people).grid(row=0, column=1, pady=3)
        ttk.Label(self.dining_box, text="예산").grid(row=1, column=0, padx=6, pady=3)
        self.budget_combo = ttk.Combobox(
            self.dining_box, width=12, state="readonly",
            values=list(PRICE_LABELS.values()))
        self.budget_combo.current(0)
        self.budget_combo.grid(row=1, column=1, pady=3)

        # 검색(A9)
        box = ttk.LabelFrame(left, text="검색")
        box.pack(fill="x", pady=6)
        ttk.Entry(box, textvariable=self.keyword, width=18).pack(padx=6, pady=4)

        self.spin_btn = tk.Button(
            left, text="룰렛 돌리기!", font=theme.FONT_BIG, bg=theme.TOMATO,
            fg="white", activebackground=theme.TOMATO_SHADOW,
            relief="flat", command=self.spin, cursor="hand2")
        self.spin_btn.pack(fill="x", pady=(10, 4), ipady=6)

        # 오른쪽: 마스코트 + 룰렛 + 결과
        top = ttk.Frame(right)
        top.pack(fill="x")
        self.mascot_label = tk.Label(top, bg=theme.CREAM)
        self.mascot_label.pack(side="left", padx=4)
        self.status = tk.Label(top, text="오늘 뭐 먹지? 버튼을 눌러요!",
                               font=theme.FONT_TITLE, bg=theme.CREAM, fg=theme.NORI)
        self.status.pack(side="left", padx=8)
        self._set_mascot("jb_mascot.png")

        self.wheel = RouletteCanvas(right, size=300)
        self.wheel.pack(pady=4)

        self.result_card = tk.Frame(right, bg=theme.WHITE,
                                    highlightbackground=theme.RICE_EDGE,
                                    highlightthickness=2)
        self.result_text = tk.Label(self.result_card, text="", font=theme.FONT_BIG,
                                    bg=theme.WHITE, fg=theme.TOMATO_SHADOW,
                                    wraplength=420, justify="left")
        self.result_text.pack(anchor="w", padx=10, pady=(8, 2))
        self.result_sub = tk.Label(self.result_card, text="", font=theme.FONT,
                                   bg=theme.WHITE, fg=theme.NORI,
                                   wraplength=420, justify="left")
        self.result_sub.pack(anchor="w", padx=10)
        btns = tk.Frame(self.result_card, bg=theme.WHITE)
        btns.pack(anchor="w", padx=6, pady=6)
        self.accept_btn = ttk.Button(btns, text="✅ 이걸로 결정", command=self.accept)
        self.accept_btn.pack(side="left", padx=3)
        ttk.Button(btns, text="🔄 다시", command=self.spin).pack(side="left", padx=3)
        ttk.Button(btns, text="📋 복사", command=self.copy_result).pack(side="left", padx=3)
        self.fav_btn = ttk.Button(btns, text="⭐ 즐겨찾기", command=self.toggle_favorite)
        self.fav_btn.pack(side="left", padx=3)
        ttk.Button(btns, text="🚫 제외", command=self.exclude_winner).pack(side="left", padx=3)

        self._on_mode_change()

    def _set_mascot(self, name: str) -> None:
        img = theme.image(name)
        if img:
            self.mascot_label.configure(image=img)
            self.mascot_label.image = img

    def _rebuild_categories(self) -> None:
        for w in self.cat_box.winfo_children():
            w.destroy()
        selected = {c for c, v in self.cat_vars.items() if v.get()}
        if self.mode.get() == MODE_MENU:
            cats = sorted({m.category for m in self.app.store.menus})
        else:
            cats = sorted({r.category for r in self.app.store.all_restaurants()})
        self.cat_vars = {}
        row = tk.Frame(self.cat_box)
        row.pack(anchor="w")
        for i, cat in enumerate(cats):
            if i and i % 3 == 0:
                row = tk.Frame(self.cat_box)
                row.pack(anchor="w")
            var = tk.BooleanVar(value=cat in selected)
            self.cat_vars[cat] = var
            ttk.Checkbutton(row, text=cat, variable=var).pack(side="left", padx=4)

    def _on_mode_change(self) -> None:
        if self.mode.get() == MODE_DINING:
            self.dining_box.pack(fill="x", pady=6, after=self.cat_box)
        else:
            self.dining_box.pack_forget()
        self._rebuild_categories()

    def refresh_weather_from_file(self) -> None:
        """weather.txt 값(오늘자만 유효)을 초기 토글값으로. 수동 변경이 우선."""
        w = self.app.store.weather_file
        if w:
            self.weather.set(w)

    # ---------------------------------------------------------- 추첨
    def build_query(self) -> Query:
        cats = {c for c, v in self.cat_vars.items() if v.get()}
        budget = self.budget_combo.current()  # 0=전체
        return Query(
            mode=self.mode.get(), categories=cats, weather=self.weather.get(),
            walk_limit=self.app.cfg.default_walk_limit,
            people=self.people.get() if self.mode.get() == MODE_DINING else None,
            max_price=budget if (self.mode.get() == MODE_DINING and budget) else None,
            keyword=self.keyword.get(), cooldown_days=self.app.cfg.cooldown_days)

    def spin(self) -> None:
        if self.wheel.spinning:
            return
        self._rebuild_categories()
        self.candidates, self.notes = rec.collect_with_relaxation(
            self.app.store, self.build_query())
        self.result_card.pack_forget()
        if not self.candidates:
            # 빈 상태(기획안 7-A): 배고픈 마스코트가 데이터 추가를 안내
            self._set_mascot("jb_mascot_hungry.png")
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
        self._set_mascot("jb_mascot_dizzy.png")
        self.wheel.set_candidates([s.name for s in self.slots])
        self.wheel.spin_to(idx, self._on_spin_done)

    def _on_spin_done(self) -> None:
        self._set_mascot("jb_mascot_happy.png")
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
        self.accept_btn.state(["!disabled"])
        self.result_card.pack(fill="x", pady=6)

    # ---------------------------------------------------------- 결과 액션
    def accept(self) -> None:
        if not self.winner:
            return
        ok = self.app.store.record_history(self.mode.get(), self.winner.name)
        self.accept_btn.state(["disabled"])
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
            self.fav_btn.configure(text="⭐ 즐겨찾기 해제")
        else:
            self.fav_btn.configure(text="⭐ 즐겨찾기")

    def exclude_winner(self) -> None:
        if not self.winner:
            return
        self.app.store.set_excluded(self.winner.name, True)
        self.status.configure(text=f"'{self.winner.name}' 제외 목록에 추가 "
                                   "(설정 탭에서 해제 가능)")
