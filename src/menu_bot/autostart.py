"""Windows 시작프로그램 등록 (관리자 권한 불필요 — shell:startup 바로가기)."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

APP_NAME = "밥봇JB"


def _shortcut_path() -> Path:
    startup = Path(os.environ.get("APPDATA", "")) / \
        "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
    return startup / f"{APP_NAME}.lnk"


def is_enabled() -> bool:
    return _shortcut_path().exists()


def set_enabled(on: bool) -> tuple[bool, str]:
    """성공 여부와 실패 사유를 반환. exe 빌드에서만 등록 가능."""
    lnk = _shortcut_path()
    try:
        if not on:
            if lnk.exists():
                lnk.unlink()
            return True, ""
        if not getattr(sys, "frozen", False):
            return False, "exe 빌드에서만 지원돼요 (개발 모드)"
        target = sys.executable
        ps = (
            "$ws = New-Object -ComObject WScript.Shell; "
            f"$s = $ws.CreateShortcut('{lnk}'); "
            f"$s.TargetPath = '{target}'; "
            f"$s.WorkingDirectory = '{Path(target).parent}'; "
            "$s.Save()"
        )
        subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps],
            check=True, capture_output=True,
            creationflags=subprocess.CREATE_NO_WINDOW)
        return lnk.exists(), "" if lnk.exists() else "바로가기 생성 실패"
    except Exception as e:  # noqa: BLE001 — 설정 실패가 앱을 죽이면 안 됨
        return False, str(e)
