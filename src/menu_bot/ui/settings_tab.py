"""설정 — 경로/알림/동작/제외목록 4카드 (기획안 v2 5.5)."""
from __future__ import annotations

import re
import tkinter as tk
from tkinter import filedialog

import customtkinter as ctk

from .. import autostart
from ..config import save_config
from . import theme, widgets

TIME_RE = re.compile(r"^([01]?\d|2[0-3]):[0-5]\d$")


class SettingsTab(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self._build()

    def _build(self) -> None:
        cfg = self.app.cfg
        grid = ctk.CTkFrame(self, fg_color="transparent")
        grid.pack(fill="both", expand=True)
        grid.grid_columnconfigure((0, 1), weight=1)
        grid.grid_rowconfigure(1, weight=1)

        entry_kw = dict(height=32, font=theme.font(11), fg_color=theme.BG_ELEV,
                        border_color=theme.BORDER, text_color=theme.TEXT_HI)

        # 경로 카드
        path_card = widgets.Card(grid, title="데이터 경로", hoverable=False)
        path_card.grid(row=0, column=0, sticky="nsew", padx=(0, 6), pady=(0, 8))
        self.data_path = self._path_row(path_card, "공유 데이터 폴더", cfg.data_path, entry_kw)
        self.personal_path = self._path_row(
            path_card, "개인 데이터 폴더 (비우면 공유와 동일)", cfg.personal_path, entry_kw)

        # 알림 카드
        notify_card = widgets.Card(grid, title="알림", hoverable=False)
        notify_card.grid(row=0, column=1, sticky="nsew", padx=(6, 0), pady=(0, 8))
        self.lunch = self._entry_row(notify_card, "점심 알림 (HH:MM)",
                                     cfg.notify_lunch, entry_kw)
        self.dinner = self._entry_row(notify_card, "저녁 알림 (HH:MM)",
                                      cfg.notify_dinner, entry_kw)

        # 동작 카드
        behave_card = widgets.Card(grid, title="동작", hoverable=False)
        behave_card.grid(row=1, column=0, sticky="nsew", padx=(0, 6))
        self.cooldown = self._entry_row(behave_card, "중복 방지 일수",
                                        str(cfg.cooldown_days), entry_kw)
        self.walk = self._entry_row(behave_card, "우천 시 도보 제한(분)",
                                    str(cfg.default_walk_limit), entry_kw)
        self.autostart_var = tk.BooleanVar(value=autostart.is_enabled())
        ctk.CTkSwitch(behave_card, text="Windows 시작 시 자동 실행 (알림 권장)",
                      variable=self.autostart_var, font=theme.font(11),
                      progress_color=theme.TOMATO,
                      text_color=theme.TEXT_MID).pack(anchor="w", padx=16, pady=8)

        # 제외 목록 카드
        ex_card = widgets.Card(grid, title="제외 목록 — 더블클릭으로 해제", hoverable=False)
        ex_card.grid(row=1, column=1, sticky="nsew", padx=(6, 0))
        self.ex_list = widgets.ListPanel(ex_card, height=150)
        self.ex_list.pack(fill="both", expand=True, padx=10, pady=(0, 12))

        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.pack(fill="x", pady=(10, 0))
        self.msg = ctk.CTkLabel(bottom, text=f"v{cfg.version} · 설정: {cfg.config_path()}",
                                font=theme.font(10), text_color=theme.TEXT_DIM)
        self.msg.pack(side="left")
        ctk.CTkButton(bottom, text="저장", width=110, height=36, corner_radius=18,
                      font=theme.font(12, bold=True), fg_color=theme.TOMATO,
                      hover_color=theme.TOMATO_HOVER, text_color="#FFFFFF",
                      command=self.save).pack(side="right")

    def _entry_row(self, parent, label: str, value: str, entry_kw) -> ctk.CTkEntry:
        ctk.CTkLabel(parent, text=label, font=theme.font(11),
                     text_color=theme.TEXT_MID, anchor="w").pack(
            fill="x", padx=16, pady=(6, 0))
        e = ctk.CTkEntry(parent, **entry_kw)
        e.insert(0, value)
        e.pack(fill="x", padx=16, pady=(2, 4))
        return e

    def _path_row(self, parent, label: str, value: str, entry_kw) -> ctk.CTkEntry:
        ctk.CTkLabel(parent, text=label, font=theme.font(11),
                     text_color=theme.TEXT_MID, anchor="w").pack(
            fill="x", padx=16, pady=(6, 0))
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=(2, 4))
        e = ctk.CTkEntry(row, **entry_kw)
        e.insert(0, value)
        e.pack(side="left", fill="x", expand=True)

        def browse():
            d = filedialog.askdirectory()
            if d:
                e.delete(0, "end")
                e.insert(0, d)

        ctk.CTkButton(row, text="…", width=34, height=32, corner_radius=8,
                      fg_color=theme.BG_ELEV, hover_color=theme.BG_HOVER,
                      text_color=theme.TEXT_HI, command=browse).pack(
            side="right", padx=(6, 0))
        return e

    def refresh(self) -> None:
        self.ex_list.clear()
        excluded = self.app.store.excluded
        if not excluded:
            self.ex_list.add_row("제외된 항목이 없어요")
            return
        for name in excluded:
            self.ex_list.add_row(name, on_double=self._remove_excluded)

    def _remove_excluded(self, name: str) -> None:
        self.app.store.set_excluded(name, False)
        self.refresh()

    def save(self) -> None:
        cfg = self.app.cfg
        for entry, label in ((self.lunch, "점심"), (self.dinner, "저녁")):
            if not TIME_RE.match(entry.get().strip()):
                self.msg.configure(text=f"⚠️ {label} 알림 시각은 HH:MM 형식이어야 해요",
                                   text_color=theme.WARN)
                return
        try:
            cooldown = max(0, int(self.cooldown.get()))
            walk = max(1, int(self.walk.get()))
        except ValueError:
            self.msg.configure(text="⚠️ 일수/도보 제한은 숫자여야 해요",
                               text_color=theme.WARN)
            return
        cfg.data_path = self.data_path.get().strip() or r".\data"
        cfg.personal_path = self.personal_path.get().strip()
        cfg.notify_lunch = self.lunch.get().strip()
        cfg.notify_dinner = self.dinner.get().strip()
        cfg.cooldown_days = cooldown
        cfg.default_walk_limit = walk
        save_config(cfg)
        ok, detail = autostart.set_enabled(self.autostart_var.get())
        self.app.apply_settings()
        text = "✅ 저장했어요!"
        if not ok:
            text += f" (자동 실행 설정 실패: {detail})"
        self.msg.configure(text=text,
                           text_color=theme.SUCCESS if ok else theme.WARN)
