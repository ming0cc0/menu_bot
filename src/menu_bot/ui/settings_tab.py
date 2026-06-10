"""설정 탭: 경로/알림/쿨다운/자동시작/제외목록 관리."""
from __future__ import annotations

import re
import tkinter as tk
from tkinter import filedialog, ttk

from .. import autostart
from ..config import save_config
from . import theme

TIME_RE = re.compile(r"^([01]?\d|2[0-3]):[0-5]\d$")


class SettingsTab(ttk.Frame):
    def __init__(self, master, app):
        super().__init__(master)
        self.app = app
        self._build()

    def _build(self) -> None:
        cfg = self.app.cfg
        form = ttk.LabelFrame(self, text="설정")
        form.pack(fill="x", padx=12, pady=10)

        self.data_path = self._path_row(form, 0, "공유 데이터 폴더", cfg.data_path)
        self.personal_path = self._path_row(
            form, 1, "개인 데이터 폴더 (비우면 공유와 동일)", cfg.personal_path)
        self.lunch = self._entry_row(form, 2, "점심 알림 시각 (HH:MM)", cfg.notify_lunch)
        self.dinner = self._entry_row(form, 3, "저녁 알림 시각 (HH:MM)", cfg.notify_dinner)
        self.cooldown = self._entry_row(form, 4, "중복 방지 일수", str(cfg.cooldown_days))
        self.walk = self._entry_row(form, 5, "우천 시 도보 제한(분)", str(cfg.default_walk_limit))

        self.autostart_var = tk.BooleanVar(value=autostart.is_enabled())
        ttk.Checkbutton(form, text="Windows 시작 시 자동 실행 (알림을 받으려면 권장)",
                        variable=self.autostart_var).grid(
            row=6, column=0, columnspan=3, sticky="w", padx=8, pady=4)

        ttk.Button(form, text="저장", command=self.save).grid(
            row=7, column=2, sticky="e", padx=8, pady=8)
        self.msg = tk.Label(self, text="", font=theme.FONT, fg=theme.NORI)
        self.msg.pack(padx=12, anchor="w")

        ex_box = ttk.LabelFrame(self, text="제외 목록 (더블클릭으로 해제)")
        ex_box.pack(fill="both", expand=True, padx=12, pady=6)
        self.ex_list = tk.Listbox(ex_box, font=theme.FONT, height=5)
        self.ex_list.pack(fill="both", expand=True, padx=4, pady=4)
        self.ex_list.bind("<Double-Button-1>", self._remove_excluded)

        info = (f"버전 {cfg.version} · 설정 파일: {cfg.config_path()}\n"
                "데이터 파일은 메모장으로 직접 수정할 수 있어요 (UTF-8).")
        tk.Label(self, text=info, font=theme.FONT, fg=theme.RICE_EDGE,
                 justify="left").pack(padx=12, pady=4, anchor="w")

    def _entry_row(self, parent, row: int, label: str, value: str) -> ttk.Entry:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=8, pady=3)
        e = ttk.Entry(parent, width=34)
        e.insert(0, value)
        e.grid(row=row, column=1, sticky="w", padx=4, pady=3)
        return e

    def _path_row(self, parent, row: int, label: str, value: str) -> ttk.Entry:
        e = self._entry_row(parent, row, label, value)

        def browse():
            d = filedialog.askdirectory()
            if d:
                e.delete(0, "end")
                e.insert(0, d)

        ttk.Button(parent, text="…", width=3, command=browse).grid(
            row=row, column=2, padx=4)
        return e

    def refresh(self) -> None:
        self.ex_list.delete(0, "end")
        for name in self.app.store.excluded:
            self.ex_list.insert("end", name)

    def _remove_excluded(self, _event) -> None:
        sel = self.ex_list.curselection()
        if sel:
            self.app.store.set_excluded(self.ex_list.get(sel[0]), False)
            self.refresh()

    def save(self) -> None:
        cfg = self.app.cfg
        for entry, label in ((self.lunch, "점심"), (self.dinner, "저녁")):
            if not TIME_RE.match(entry.get().strip()):
                self.msg.configure(text=f"⚠️ {label} 알림 시각은 HH:MM 형식이어야 해요",
                                   fg=theme.TOMATO)
                return
        try:
            cooldown = max(0, int(self.cooldown.get()))
            walk = max(1, int(self.walk.get()))
        except ValueError:
            self.msg.configure(text="⚠️ 일수/도보 제한은 숫자여야 해요", fg=theme.TOMATO)
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
        self.msg.configure(text=text, fg=theme.NORI)
