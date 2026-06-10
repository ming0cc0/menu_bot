"""공통 컴포넌트 — Card / Chip / Stepper / ListPanel / 모션 헬퍼 (기획안 v2 6장)."""
from __future__ import annotations

import tkinter as tk
from typing import Callable

import customtkinter as ctk

from . import theme


# ---------------------------------------------------------------- 모션
def ease_out_cubic(t: float) -> float:
    return 1 - (1 - t) ** 3


def animate(widget, frames: int, ms_total: int, on_frame: Callable[[float], None],
            on_done: Callable[[], None] | None = None) -> None:
    """after 기반 프레임 보간. on_frame(eased_t 0→1). widget 파괴 시 중단."""
    interval = max(10, ms_total // frames)

    def step(frame: int = 1) -> None:
        if not widget.winfo_exists():
            return
        on_frame(ease_out_cubic(frame / frames))
        if frame < frames:
            widget.after(interval, step, frame + 1)
        elif on_done:
            on_done()

    step()


def count_up(label: ctk.CTkLabel, n: int, suffix: str = "회") -> None:
    """이력 통계 숫자 카운트업 (300ms, 12스텝)."""
    animate(label, 12, 300,
            lambda t: label.configure(text=f"{round(n * t)}{suffix}"))


# ---------------------------------------------------------------- Card
class Card(ctk.CTkFrame):
    """벤토 카드 — radius 14, 1px 보더, 호버 시 토마토 틴트 글로우."""

    def __init__(self, master, title: str | None = None, hoverable: bool = True, **kw):
        kw.setdefault("fg_color", theme.BG_CARD)
        kw.setdefault("corner_radius", theme.RADIUS_CARD)
        kw.setdefault("border_width", 1)
        kw.setdefault("border_color", theme.BORDER)
        super().__init__(master, **kw)
        if title:
            ctk.CTkLabel(self, text=title, font=theme.font(12, bold=True),
                         text_color=theme.TEXT_DIM, anchor="w").pack(
                fill="x", padx=16, pady=(12, 2))
        if hoverable:
            self.bind("<Enter>", self._on_enter, add="+")
            self.bind("<Leave>", self._on_leave, add="+")

    def _on_enter(self, _e) -> None:
        self.configure(border_color=theme.BORDER_GLOW)

    def _on_leave(self, _e) -> None:
        self.configure(border_color=theme.BORDER)


# ---------------------------------------------------------------- Chip
class Chip(ctk.CTkButton):
    """필 토글 칩 — 선택 시 '✓ ' 접두 + 토마토 소프트 (색상 단독 구분 금지)."""

    def __init__(self, master, text: str, variable: tk.BooleanVar,
                 command: Callable[[], None] | None = None):
        self._text = text
        self._var = variable
        self._user_command = command
        super().__init__(master, text=text, font=theme.font(11),
                         corner_radius=theme.RADIUS_PILL, height=28,
                         border_width=1, command=self._toggle)
        self._apply()

    def _toggle(self) -> None:
        self._var.set(not self._var.get())
        self._apply()
        if self._user_command:
            self._user_command()

    def _apply(self) -> None:
        if self._var.get():
            self.configure(text=f"✓ {self._text}", fg_color=theme.TOMATO_SOFT,
                           hover_color=theme.TOMATO_SOFT,
                           border_color=theme.TOMATO,
                           text_color=theme.TOMATO_HOVER)
        else:
            self.configure(text=self._text, fg_color=theme.BG_ELEV,
                           hover_color=theme.BG_HOVER,
                           border_color=theme.BORDER,
                           text_color=theme.TEXT_MID)


# ---------------------------------------------------------------- Stepper
class Stepper(ctk.CTkFrame):
    """[−] n [+] — CTk에 Spinbox가 없어 직접 구성."""

    def __init__(self, master, variable: tk.IntVar, from_: int, to: int, width: int = 110):
        super().__init__(master, fg_color=theme.BG_ELEV,
                         corner_radius=theme.RADIUS_PILL, width=width, height=30)
        self._var, self._min, self._max = variable, from_, to
        btn_kw = dict(width=28, height=24, corner_radius=theme.RADIUS_PILL,
                      fg_color="transparent", hover_color=theme.BG_HOVER,
                      text_color=theme.TEXT_HI, font=theme.font(13, bold=True))
        ctk.CTkButton(self, text="−", command=lambda: self._bump(-1),
                      **btn_kw).pack(side="left", padx=(4, 0), pady=3)
        self._label = ctk.CTkLabel(self, textvariable=variable,
                                   font=theme.font(12, bold=True),
                                   text_color=theme.TEXT_HI, width=34)
        self._label.pack(side="left", expand=True)
        ctk.CTkButton(self, text="+", command=lambda: self._bump(1),
                      **btn_kw).pack(side="right", padx=(0, 4), pady=3)

    def _bump(self, d: int) -> None:
        self._var.set(min(self._max, max(self._min, self._var.get() + d)))


# ---------------------------------------------------------------- ListPanel
class ListPanel(ctk.CTkScrollableFrame):
    """tk.Listbox 대체 — 행 hover/더블클릭 지원 스크롤 패널."""

    def __init__(self, master, height: int = 180, **kw):
        kw.setdefault("fg_color", "transparent")
        super().__init__(master, height=height, **kw)
        self._rows: list[ctk.CTkFrame] = []

    def clear(self) -> None:
        for row in self._rows:
            row.destroy()
        self._rows = []

    def add_row(self, text: str, sub: str = "",
                on_double: Callable[[str], None] | None = None,
                bar_ratio: float | None = None) -> None:
        row = ctk.CTkFrame(self, fg_color=theme.BG_ELEV, corner_radius=8)
        row.pack(fill="x", pady=2, padx=2)
        label = ctk.CTkLabel(row, text=text, font=theme.font(11),
                             text_color=theme.TEXT_HI, anchor="w")
        label.pack(side="left", fill="x", expand=True, padx=10, pady=6)
        if sub:
            ctk.CTkLabel(row, text=sub, font=theme.font(10),
                         text_color=theme.TEXT_DIM).pack(side="right", padx=10)
        if bar_ratio is not None:
            bar = ctk.CTkProgressBar(row, width=90, height=6,
                                     progress_color=theme.TOMATO,
                                     fg_color=theme.BG_CARD)
            bar.set(max(0.04, min(1.0, bar_ratio)))
            bar.pack(side="right", padx=10)
        widgets = [row, label]
        for w in widgets:
            w.bind("<Enter>", lambda _e, r=row: r.configure(fg_color=theme.BG_HOVER), add="+")
            w.bind("<Leave>", lambda _e, r=row: r.configure(fg_color=theme.BG_ELEV), add="+")
            if on_double:
                w.bind("<Double-Button-1>", lambda _e, t=text: on_double(t), add="+")
        self._rows.append(row)
