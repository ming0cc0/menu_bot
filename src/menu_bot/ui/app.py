"""메인 윈도우 — 헤더 + 탭, 트레이 이벤트 큐 폴링, 닫기=트레이 숨김."""
from __future__ import annotations

import queue
import tkinter as tk
from tkinter import messagebox, ttk

from ..config import Config
from ..data_loader import DataStore, ensure_sample_data
from . import theme
from .help_tab import HelpTab
from .history_tab import HistoryTab
from .recommend_tab import RecommendTab
from .settings_tab import SettingsTab
from .suggest_tab import SuggestTab
from .vote_tab import VoteTab

POLL_MS = 200


class MenuBotApp(tk.Tk):
    def __init__(self, cfg: Config, first_run: bool = False):
        super().__init__()
        self.cfg = cfg
        self.store = DataStore(cfg.data_dir, cfg.personal_dir)
        self.events: queue.Queue[str] = queue.Queue()
        self._hide_notice_shown = False
        self._quitting = False

        self.title("밥봇 JB — 오늘 뭐 먹지?")
        self.configure(bg=theme.CREAM)
        self.geometry("760x640")
        self.minsize(680, 560)
        icon = theme.image("jb_app_icon_256.png")
        if icon:
            self.iconphoto(True, icon)

        self._build_header()
        self._build_tabs()
        self.protocol("WM_DELETE_WINDOW", self.hide_to_tray)
        self.after(POLL_MS, self._poll_events)
        if first_run:
            self.after(400, self._show_onboarding)

    # ------------------------------------------------------------ UI
    def _build_header(self) -> None:
        header = tk.Frame(self, bg=theme.CREAM)
        header.pack(fill="x", padx=10, pady=(8, 0))
        logo = theme.image("jb_logo.png")
        if logo:
            lbl = tk.Label(header, image=logo, bg=theme.CREAM)
            lbl.image = logo
            lbl.pack(side="left")
        tk.Label(header, text="밥봇 JB", font=("Malgun Gothic", 16, "bold"),
                 bg=theme.CREAM, fg=theme.TOMATO).pack(side="left", padx=8)
        tk.Label(header, text="여의도 한정 메뉴 결정 도우미",
                 font=theme.FONT, bg=theme.CREAM,
                 fg=theme.NORI).pack(side="left", padx=4, pady=(6, 0))

    def _build_tabs(self) -> None:
        style = ttk.Style(self)
        style.configure("TNotebook", background=theme.CREAM)
        style.configure("TFrame", background=theme.CREAM)
        style.configure("TLabelframe", background=theme.CREAM)
        style.configure("TLabelframe.Label", background=theme.CREAM,
                        foreground=theme.NORI, font=theme.FONT_BOLD)
        style.configure("TLabel", background=theme.CREAM, font=theme.FONT)
        style.configure("TRadiobutton", background=theme.CREAM, font=theme.FONT)
        style.configure("TCheckbutton", background=theme.CREAM, font=theme.FONT)

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=8, pady=8)
        self.recommend = RecommendTab(nb, self)
        self.vote = VoteTab(nb, self)
        self.suggest = SuggestTab(nb, self)
        self.history = HistoryTab(nb, self)
        self.settings = SettingsTab(nb, self)
        self.help = HelpTab(nb, self)
        for tab, label in ((self.recommend, "🎰 추천"), (self.vote, "🗳️ 투표"),
                           (self.suggest, "✍️ 맛집 등록"), (self.history, "📊 이력"),
                           (self.settings, "⚙️ 설정"), (self.help, "❓ 도움말")):
            nb.add(tab, text=label)
        nb.bind("<<NotebookTabChanged>>", self._on_tab_change)

    def _on_tab_change(self, event) -> None:
        current = event.widget.nametowidget(event.widget.select())
        if current is self.history:
            self.history.refresh()
        elif current is self.settings:
            self.settings.refresh()

    def _show_onboarding(self) -> None:
        messagebox.showinfo(
            "밥봇 JB에 어서오세요! 🍙",
            "처음 실행이라 샘플 맛집/메뉴 데이터를 만들어 뒀어요.\n\n"
            "1. [추천] 탭에서 '룰렛 돌리기!'를 눌러보세요.\n"
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
