"""중복 실행 방지 + 두 번째 실행 시 기존 창 띄우기.

- mutex(ctypes)로 단일 인스턴스 보장
- 로컬 소켓으로 'SHOW' 신호 전달 (트레이 상주 중 더블클릭/토스트 클릭 대응)
"""
from __future__ import annotations

import ctypes
import logging
import socket
import threading
from typing import Callable

log = logging.getLogger(__name__)

MUTEX_NAME = "Local\\BapBotJB_SingleInstance"
PORT = 47917  # localhost 전용
ERROR_ALREADY_EXISTS = 183

_mutex_handle = None


def acquire() -> bool:
    """첫 인스턴스면 True. 핸들은 프로세스 종료까지 유지된다."""
    global _mutex_handle
    _mutex_handle = ctypes.windll.kernel32.CreateMutexW(None, False, MUTEX_NAME)
    return ctypes.windll.kernel32.GetLastError() != ERROR_ALREADY_EXISTS


def notify_existing() -> None:
    """두 번째 인스턴스: 기존 인스턴스에게 창을 띄우라고 알리고 끝낸다."""
    try:
        with socket.create_connection(("127.0.0.1", PORT), timeout=1.0) as s:
            s.sendall(b"SHOW")
    except OSError as e:
        log.warning("기존 인스턴스 신호 전달 실패: %s", e)


def listen(on_show: Callable[[], None]) -> None:
    """첫 인스턴스: SHOW 신호 수신 서버(데몬 스레드).

    on_show는 다른 스레드에서 불리므로 큐 등 스레드 안전한 방법으로
    UI에 전달해야 한다.
    """
    def server() -> None:
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            srv.bind(("127.0.0.1", PORT))
            srv.listen(2)
        except OSError as e:
            log.warning("단일 인스턴스 수신 서버 시작 실패: %s", e)
            return
        while True:
            try:
                conn, _ = srv.accept()
                with conn:
                    if conn.recv(16).startswith(b"SHOW"):
                        try:
                            on_show()
                        except Exception as e:  # noqa: BLE001 — 수신 루프는 죽으면 안 됨
                            log.warning("창 표시 콜백 실패: %s", e)
            except OSError:
                continue

    threading.Thread(target=server, daemon=True, name="single-instance").start()
