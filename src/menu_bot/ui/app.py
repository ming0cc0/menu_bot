"""메인 윈도우 — 사이드바 내비게이션 + 콘텐츠 영역 (기획안 v2 5.1).

트레이/IPC 이벤트는 큐 + after 폴링으로만 UI에 전달한다 (스레드 규칙 유지).
"""
from __future__ import annotations

import queue
from tkinter import messagebox

import customtkinter as ctk

from ..config import Config
from ..data_loader import DataStore, ensure_sample_data
from . import theme, widgets
from .help_tab import HelpTab
from .history_tab import HistoryTab
from .recommend_tab import RecommendTab
from .settings_tab import SettingsTab
from .suggest_tab import SuggestTab
from .vote_tab import VoteTab

POLL_MS = 200
BLINK_EVERY_MS = 4000
BLINK_HOLD_MS = 160
SIDEBAR_W = 190

NAV = [("recommend", "🎰  추천"), ("vote", "🗳  투표"), ("suggest", "✍  맛집 등록"),
       ("history", "📊  이력"), ("settings", "⚙  설정"), ("help", "❓  도움말")]


class MenuBotApp(ctk.CTk):
    def __init__(self, cfg: Config, first_run: bool = False):
        theme.init_appearance()  # 루트 생성 전 다크 고정 — 흰 플래시 방지
        super().__init__(fg_color=theme.BG_BASE)
        self.cfg = cfg
        self.store = DataStore(cfg.data_dir, cfg.personal_dir)
        self.events: queue.Queue[str] = queue.Queue()
        self._hide_notice_shown = False
        self._quitting = False

        self.title("밥봇 JB — 오늘 뭐 먹지?")
        self.geometry("1000x680")
        self.minsize(900, 620)
        icon = theme.image("jb_app_icon_256.png")
        if icon:
            self.iconphoto(True, icon)

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._build_sidebar()
        self._build_views()
        self.show_view("recommend")

        self.protocol("WM_DELETE_WINDOW", self.hide_to_tray)
        self.after(POLL_MS, self._poll_events)
        self.after(BLINK_EVERY_MS, self._blink)
        if first_run:
            self.after(400, self._show_onboarding)

    # ------------------------------------------------------------ 사이드바
    def _build_sidebar(self) -> None:
        bar = ctk.CTkFrame(self, fg_color=theme.BG_SIDEBAR, corner_radius=0,
                           width=SIDEBAR_W)
        bar.grid(row=0, column=0, sticky="nsw")
        bar.grid_propagate(False)
        self._sidebar = bar

        head = ctk.CTkFrame(bar, fg_color="transparent")
        head.pack(fill="x", padx=16, pady=(20, 24))
        logo = theme.ctk_image("jb_logo_dark.png", height=30)
        if logo:
            ctk.CTkLabel(head, image=logo, text="").pack(side="left")
        ctk.CTkLabel(head, text="밥봇 JB", font=theme.font(15, bold=True),
                     text_color=theme.TEXT_HI).pack(side="left", padx=8)

        self._nav_buttons: dict[str, ctk.CTkButton] = {}
        self._nav_frame = ctk.CTkFrame(bar, fg_color="transparent")
        self._nav_frame.pack(fill="x", padx=10)
        for name, label in NAV:
            btn = ctk.CTkButton(
                self._nav_frame, text=label, anchor="w", height=38,
                corner_radius=10, fg_color="transparent",
                hover_color=theme.BG_HOVER, text_color=theme.TEXT_MID,
                font=theme.font(12), command=lambda n=name: self.show_view(n))
            btn.pack(fill="x", pady=2)
            self._nav_buttons[name] = btn
        # 활성 인디케이터 (4px 토마토 바 — show_view에서 슬라이드)
        self._indicator = ctk.CTkFrame(self._nav_frame, width=4, height=22,
                                       fg_color=theme.TOMATO, corner_radius=2)

        foot = ctk.CTkFrame(bar, fg_color="transparent")
        foot.pack(side="bottom", fill="x", pady=18)
        self._mascot_label = ctk.CTkLabel(foot, text="",
                                          image=theme.mascot("base", 88))
        self._mascot_label.pack()
        ctk.CTkLabel(foot, text=f"v{self.cfg.version}", font=theme.font(10),
                     text_color=theme.TEXT_DIM).pack(pady=(6, 0))

    def _blink(self) -> None:
        """마스코트 아이들 깜빡임 — 4초 주기."""
        if self._quitting or not self.winfo_exists():
            return
        self._mascot_label.configure(image=theme.mascot("blink", 88))
        self.after(BLINK_HOLD_MS,
                   lambda: self._mascot_label.configure(image=theme.mascot("base", 88))
                   if self._mascot_label.winfo_exists() else None)
        self.after(BLINK_EVERY_MS, self._blink)

    # ------------------------------------------------------------ 뷰
    def _build_views(self) -> None:
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.grid(row=0, column=1, sticky="nsew", padx=16, pady=14)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        self.recommend = RecommendTab(container, self)
        self.vote = VoteTab(container, self)
        self.suggest = SuggestTab(container, self)
        self.history = HistoryTab(container, self)
        self.settings = SettingsTab(container, self)
        self.help = HelpTab(container, self)
        self._views = {"recommend": self.recommend, "vote": self.vote,
                       "suggest": self.suggest, "history": self.history,
                       "settings": self.settings, "help": self.help}
        for view in self._views.values():
            view.grid(row=0, column=0, sticky="nsew")

    def show_view(self, name: str) -> None:
        view = self._views[name]
        view.tkraise()
        for n, btn in self._nav_buttons.items():
            active = n == name
            btn.configure(text_color=theme.TEXT_HI if active else theme.TEXT_MID,
                          fg_color=theme.BG_ELEV if active else "transparent")
        self._slide_indicator(name)
        if name == "history":
            self.history.refresh()
        elif name == "settings":
            self.settings.refresh()

    def _slide_indicator(self, name: str) -> None:
        btn = self._nav_buttons[name]
        self.update_idletasks()
        target_y = btn.winfo_y() + (btn.winfo_height() - 22) // 2
        start_y = self._indicator.winfo_y()
        if not self._indicator.winfo_ismapped():
            self._indicator.place(x=0, y=target_y)
            return
        widgets.animate(self._indicator, 10, 180,
                        lambda t: self._indicator.place(x=0, y=round(start_y + (target_y - start_y) * t)))

    def _show_onboarding(self) -> None:
        messagebox.showinfo(
            "밥봇 JB에 어서오세요! 🍙",
            "처음 실행이라 샘플 맛집/메뉴 데이터를 만들어 뒀어요.\n\n"
            "1. [추천]에서 '룰렛 돌리기!'를 눌러보세요.\n"
            "2. data 폴더의 txt 파일을 메모장으로 열어 우리 회사 주변\n"
            "   맛집으로 바꿔주세요.\n"
            "3. 매일 알림을 받으려면 [설정]에서 '시작 시 자동 실행'을 켜두세요!",
            parent=self)

    # ------------------------------------------------------------ 트레이 연동
    def post_event(self, name: str) -> None:
        """다른 스레드(트레이/IPC)에서 호출하는 유일한 진입점."""
        self.events.put(name)

    def _poll_events(self) -> None:
        try:
            while True:
                event = self.events.get_nowait()
                if event == "show":
                    self.show_window()
                elif event == "spin":
                    self.show_window()
                    self.show_view("recommend")
                    self.recommend.spin()
                elif event == "quit":
                    self.quit_app()
        except queue.Empty:
            pass
        if not self._quitting:
            self.after(POLL_MS, self._poll_events)

    def show_window(self) -> None:
        self.deiconify()
        self.lift()
        self.attributes("-topmost", True)
        self.after(150, lambda: self.attributes("-topmost", False))
        self.focus_force()

    def hide_to_tray(self) -> None:
        self.recommend.wheel.stop()  # 숨김 중 연출 정지
        self.withdraw()
        if not self._hide_notice_shown:
            self._hide_notice_shown = True
            from ..notifier import send_toast
            send_toast("밥봇 JB", "트레이에서 계속 실행 중이에요. "
                                  "완전 종료는 트레이 아이콘 우클릭 → 종료")

    def quit_app(self) -> None:
        self._quitting = True
        self.quit()

    # ------------------------------------------------------------ 설정 반영
    def apply_settings(self) -> None:
        ensure_sample_data(self.cfg.data_dir, self.cfg.personal_dir)
        self.store = DataStore(self.cfg.data_dir, self.cfg.personal_dir)
        self.recommend.refresh_weather_from_file()
