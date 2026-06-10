"""직원 추천 등록 탭 (F4). 개인정보 최소화: 닉네임만 받는다."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from . import theme

CATEGORIES = ["한식", "중식", "일식", "양식", "분식", "기타"]


class SuggestTab(ttk.Frame):
    def __init__(self, master, app):
        super().__init__(master)
        self.app = app
        self._build()

    def _build(self) -> None:
        form = ttk.LabelFrame(self, text="맛집 추천하기")
        form.pack(padx=14, pady=12, fill="x")
        self.author = self._field(form, 0, "닉네임/부서 (익명 가능)")
        self.name = self._field(form, 1, "식당/메뉴 이름 *")
        ttk.Label(form, text="카테고리").grid(row=2, column=0, sticky="w", padx=8, pady=4)
        self.category = ttk.Combobox(form, values=CATEGORIES, state="readonly", width=28)
        self.category.current(0)
        self.category.grid(row=2, column=1, padx=8, pady=4, sticky="w")
        self.comment = self._field(form, 3, "한줄평")
        ttk.Button(form, text="등록", command=self.submit).grid(
            row=4, column=1, sticky="e", padx=8, pady=8)
        self.msg = tk.Label(self, text="등록하면 suggestions.txt에 추가되고\n"
                                       "바로 추천 후보에 합류해요.",
                            font=theme.FONT, fg=theme.NORI, justify="left")
        self.msg.pack(padx=14, anchor="w")

    def _field(self, parent, row: int, label: str) -> ttk.Entry:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=8, pady=4)
        e = ttk.Entry(parent, width=30)
        e.grid(row=row, column=1, padx=8, pady=4, sticky="w")
        return e

    def submit(self) -> None:
        name = self.name.get().strip()
        if not name:
            self.msg.configure(text="⚠️ 이름은 필수예요!", fg=theme.TOMATO)
            return
        ok = self.app.store.add_suggestion(
            self.author.get().strip() or "익명", name,
            self.category.get(), self.comment.get().strip())
        if ok:
            self.msg.configure(text=f"✅ '{name}' 등록 완료! 추천 후보에 합류했어요.",
                               fg=theme.NORI)
            self.name.delete(0, "end")
            self.comment.delete(0, "end")
        else:
            self.msg.configure(text="⚠️ 저장 실패 — 파일이 잠겨 있을 수 있어요. "
                                    "error.log 확인", fg=theme.TOMATO)
