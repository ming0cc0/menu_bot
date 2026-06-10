"""직원 추천 등록 (F4) — 중앙 1열 폼 카드 (기획안 v2 5.3). 닉네임만 수집."""
from __future__ import annotations

import customtkinter as ctk

from . import theme, widgets

CATEGORIES = ["한식", "중식", "일식", "양식", "분식", "기타"]


class SuggestTab(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self._build()

    def _build(self) -> None:
        wrap = ctk.CTkFrame(self, fg_color="transparent")
        wrap.pack(expand=True)
        card = widgets.Card(wrap, title="맛집 추천하기", hoverable=False)
        card.pack()
        body = ctk.CTkFrame(card, fg_color="transparent", width=440)
        body.pack(padx=24, pady=(4, 20))

        entry_kw = dict(width=400, height=36, font=theme.font(12),
                        fg_color=theme.BG_ELEV, border_color=theme.BORDER,
                        text_color=theme.TEXT_HI)
        self.author = ctk.CTkEntry(body, placeholder_text="닉네임/부서 (비우면 익명)",
                                   **entry_kw)
        self.author.pack(pady=5)
        self.name = ctk.CTkEntry(body, placeholder_text="식당/메뉴 이름 *", **entry_kw)
        self.name.pack(pady=5)
        self.category = ctk.CTkOptionMenu(
            body, values=CATEGORIES, width=400, height=36, font=theme.font(12),
            fg_color=theme.BG_ELEV, button_color=theme.BG_HOVER,
            button_hover_color=theme.TOMATO_PRESS, text_color=theme.TEXT_HI,
            dropdown_fg_color=theme.BG_ELEV, dropdown_hover_color=theme.BG_HOVER,
            dropdown_text_color=theme.TEXT_HI)
        self.category.pack(pady=5)
        self.comment = ctk.CTkEntry(body, placeholder_text="한줄평 (선택)", **entry_kw)
        self.comment.pack(pady=5)
        ctk.CTkButton(body, text="등록하기", height=40, corner_radius=20,
                      font=theme.font(13, bold=True), fg_color=theme.TOMATO,
                      hover_color=theme.TOMATO_HOVER, text_color="#FFFFFF",
                      command=self.submit).pack(pady=(12, 2), fill="x")
        self.msg = ctk.CTkLabel(body, text="등록하면 suggestions.txt에 추가되고\n"
                                           "바로 추천 후보에 합류해요.",
                                font=theme.font(11), text_color=theme.TEXT_DIM,
                                justify="left")
        self.msg.pack(pady=(8, 0), anchor="w")

    def submit(self) -> None:
        name = self.name.get().strip()
        if not name:
            self.msg.configure(text="⚠️ 이름은 필수예요!", text_color=theme.WARN)
            return
        ok = self.app.store.add_suggestion(
            self.author.get().strip() or "익명", name,
            self.category.get(), self.comment.get().strip())
        if ok:
            self.msg.configure(text=f"✅ '{name}' 등록 완료! 추천 후보에 합류했어요.",
                               text_color=theme.SUCCESS)
            self.name.delete(0, "end")
            self.comment.delete(0, "end")
        else:
            self.msg.configure(text="⚠️ 저장 실패 — 파일이 잠겨 있을 수 있어요. "
                                    "error.log 확인", text_color=theme.WARN)
