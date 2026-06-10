"""데스크톱 알림 스케줄 (A7).

threading.Timer 1회 예약 대신 30초 주기 폴링 — PC 절전 복귀에도 동작하고,
알림 시각을 놓쳤으면 notify_catchup_min 이내에 한해 늦게라도 보낸다.
토스트 클릭 → exe 재실행 → 단일 인스턴스 IPC가 기존 창을 띄운다.
"""
from __future__ import annotations

import logging
import sys
import threading
from datetime import date, datetime

from .config import Config
from .paths import resource_path

log = logging.getLogger(__name__)

POLL_SEC = 30
APP_ID = "밥봇 JB"

MESSAGES = {
    "점심": "오늘 점심 뭐 드실래요? 🍙 룰렛 한 판 어때요?",
    "저녁": "오늘 저녁 뭐 먹지? 🍜 밥봇이 골라드릴게요!",
}


def send_toast(title: str, message: str) -> None:
    try:
        from winotify import Notification

        icon = resource_path("assets/jb_app_icon_256.png")
        toast = Notification(
            app_id=APP_ID, title=title, msg=message,
            icon=str(icon) if icon.exists() else "")
        if getattr(sys, "frozen", False):
            toast.set_launch(sys.executable)  # 클릭 → 단일 인스턴스가 창 포커스
        toast.show()
    except Exception as e:  # noqa: BLE001 — 알림 실패가 앱을 죽이면 안 됨
        log.warning("토스트 알림 실패: %s", e)


class NotifyScheduler:
    """cfg를 참조로 들고 있어 설정 저장 즉시 새 시각이 반영된다."""

    def __init__(self, cfg: Config):
        self.cfg = cfg
        self._sent: dict[str, str] = {}  # 모드 -> 마지막 발송 날짜(ISO)
        self._stop = threading.Event()

    def start(self) -> None:
        threading.Thread(target=self._run, daemon=True, name="notify-scheduler").start()

    def stop(self) -> None:
        self._stop.set()

    def _run(self) -> None:
        while not self._stop.wait(POLL_SEC):
            self._tick(datetime.now())

    def _tick(self, now: datetime) -> None:
        today = date.today().isoformat()
        for mode, hhmm in (("점심", self.cfg.notify_lunch),
                           ("저녁", self.cfg.notify_dinner)):
            try:
                h, m = map(int, hhmm.split(":"))
            except ValueError:
                continue
            target = now.replace(hour=h, minute=m, second=0, microsecond=0)
            if now < target or self._sent.get(mode) == today:
                continue
            late_min = (now - target).total_seconds() / 60
            if late_min > max(self.cfg.notify_catchup_min, 0):
                self._sent[mode] = today  # 너무 늦음 — 오늘은 건너뜀
                continue
            send_toast("오늘 뭐 먹지?", MESSAGES[mode])
            self._sent[mode] = today
            log.info("%s 알림 발송 (%s)", mode, hhmm)
