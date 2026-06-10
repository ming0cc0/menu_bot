"""트레이 아이콘 상주 (pystray — 별도 스레드).

콜백은 pystray 스레드에서 불리므로, 반드시 큐를 통해 tkinter로 전달한다.
"""
from __future__ import annotations

import logging
from typing import Callable

log = logging.getLogger(__name__)


def start_tray(on_show: Callable[[], None], on_spin: Callable[[], None],
               on_quit: Callable[[], None]):
    """트레이 아이콘 스레드 시작. 실패 시 None(트레이 없이 동작)."""
    try:
        import pystray
        from PIL import Image

        from .paths import resource_path

        icon_path = resource_path("assets/jb_tray_icon_32.png")
        image = Image.open(icon_path)
        menu = pystray.Menu(
            pystray.MenuItem("열기", lambda: on_show(), default=True),
            pystray.MenuItem("지금 추천 🍙", lambda: on_spin()),
            pystray.MenuItem("종료", lambda: on_quit()),
        )
        icon = pystray.Icon("bapbot_jb", image, "밥봇 JB — 오늘 뭐 먹지?", menu)
        icon.run_detached()
        return icon
    except Exception as e:  # noqa: BLE001 — 트레이 실패해도 창 모드로 계속
        log.warning("트레이 아이콘 시작 실패: %s", e)
        return None
