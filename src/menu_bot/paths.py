"""실행 환경(소스/PyInstaller exe)에 따른 경로 결정."""
from __future__ import annotations

import os
import sys
from pathlib import Path


def app_dir() -> Path:
    """exe(또는 프로젝트 루트)가 있는 폴더. config/data/error.log 기준 경로."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    # src/menu_bot/paths.py -> 프로젝트 루트
    return Path(__file__).resolve().parent.parent.parent


def writable_app_dir() -> Path:
    """config/error.log를 둘 쓰기 가능한 폴더.

    exe 폴더가 읽기 전용(예: 공유 폴더에서 직접 실행)이면
    %LOCALAPPDATA%\\LunchBot 으로 폴백한다.
    """
    d = app_dir()
    try:
        probe = d / ".write_probe"
        probe.touch()
        probe.unlink()
        return d
    except OSError:
        local = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "LunchBot"
        local.mkdir(parents=True, exist_ok=True)
        return local


def resource_path(relative: str) -> Path:
    """번들 에셋 경로. --onefile 실행 시 임시 추출 폴더(_MEIPASS)를 가리킨다."""
    base = getattr(sys, "_MEIPASS", None)
    if base:
        return Path(base) / relative
    return app_dir() / relative
