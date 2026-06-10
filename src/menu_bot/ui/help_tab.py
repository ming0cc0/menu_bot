"""도움말 — 단일 카드 Textbox (기획안 v2 5.5)."""
from __future__ import annotations

import customtkinter as ctk

from .. import __version__
from . import theme, widgets

HELP_TEXT = f"""\
🍙 밥봇 JB v{__version__} — 점심/저녁 메뉴 추천 알림봇

■ 기본 사용법
  1. [추천]에서 모드(점심/저녁/회식/메뉴)를 고르고 "룰렛 돌리기!"
  2. 마음에 들면 [이걸로 결정] — 선택이 기록되고 며칠간 중복 추천이 줄어요.
  3. [복사]로 결과를 메신저에 붙여넣을 수 있어요.

■ 날씨
  비/눈을 선택하면 가까운 곳(도보 제한 이내)과 "비올때OK" 식당 위주로 추천해요.
  데이터 폴더에 weather.txt(오늘날짜 | 비)가 있으면 자동 반영돼요.

■ 그룹 투표
  [투표]에서 후보를 뽑고 팀원들이 +1/거부권으로 결정하세요.

■ 데이터 직접 수정 (메모장 OK)
  data 폴더의 txt 파일을 열어 줄을 추가하면 끝!
  restaurants.txt: 이름 | 카테고리 | 도보분 | 가격대(1~3) | 인원수용 | 태그 | 비올때OK(Y/N)
  menus.txt:       메뉴 | 카테고리 | 맵기(0~3)
  ※ 가격대: 1 = ~1만원, 2 = 1~2만원, 3 = 2만원~
  ※ 잘못된 줄은 자동으로 건너뛰고 error.log에 남아요.

■ 알림
  설정한 시각(기본 11:30 / 17:30)에 "오늘 뭐 먹지?" 알림이 떠요.
  창을 닫아도 트레이(작업표시줄 우측)에서 계속 실행 중이에요.
  완전히 종료하려면 트레이 아이콘 우클릭 → 종료.
  ※ 알림을 받으려면 [설정]에서 "Windows 시작 시 자동 실행"을 켜두세요.

■ 문의
  사내 담당자에게 연락하거나 suggestions.txt에 의견을 남겨주세요.
"""


class HelpTab(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        card = widgets.Card(self, title="도움말", hoverable=False)
        card.pack(fill="both", expand=True)
        text = ctk.CTkTextbox(card, font=theme.font(12), fg_color="transparent",
                              text_color=theme.TEXT_MID, wrap="word")
        text.insert("1.0", HELP_TEXT)
        text.configure(state="disabled")
        text.pack(fill="both", expand=True, padx=12, pady=(0, 12))
