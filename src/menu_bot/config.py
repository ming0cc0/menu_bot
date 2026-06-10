"""config.txt 로드/저장 (key = value, # 주석)."""
from __future__ import annotations

import logging
from dataclasses import dataclass, fields
from pathlib import Path

from . import __version__
from .paths import app_dir, writable_app_dir

log = logging.getLogger(__name__)

CONFIG_NAME = "config.txt"


@dataclass
class Config:
    version: str = __version__
    data_path: str = r".\data"      # 공유 데이터(restaurants/menus/suggestions/weather)
    personal_path: str = ""          # 개인 데이터(history/favorites/exclude). 비우면 data_path와 동일
    notify_lunch: str = "11:30"
    notify_dinner: str = "17:30"
    notify_catchup_min: int = 60     # 알림 시각을 놓쳤을 때 N분 이내면 늦게라도 발송
    cooldown_days: int = 3
    default_walk_limit: int = 10
    sound: str = "off"

    def _resolve(self, value: str) -> Path:
        p = Path(value)
        if not p.is_absolute():
            p = app_dir() / p
        return p

    @property
    def data_dir(self) -> Path:
        return self._resolve(self.data_path)

    @property
    def personal_dir(self) -> Path:
        return self._resolve(self.personal_path) if self.personal_path.strip() else self.data_dir

    def config_path(self) -> Path:
        # exe 옆 config.txt 우선, 없고 exe 폴더가 읽기 전용이면 %LOCALAPPDATA%\LunchBot
        primary = app_dir() / CONFIG_NAME
        if primary.exists():
            return primary
        return writable_app_dir() / CONFIG_NAME


def load_config() -> Config:
    cfg = Config()
    path = cfg.config_path()
    if not path.exists():
        save_config(cfg)
        return cfg
    try:
        text = path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        text = path.read_text(encoding="cp949", errors="replace")
    valid = {f.name: f.type for f in fields(Config)}
    for lineno, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip()
        if key not in valid:
            log.warning("config.txt %d행: 알 수 없는 키 '%s' 무시", lineno, key)
            continue
        try:
            if key in ("cooldown_days", "default_walk_limit", "notify_catchup_min"):
                setattr(cfg, key, int(value))
            else:
                setattr(cfg, key, value)
        except ValueError:
            log.warning("config.txt %d행: '%s' 값 '%s' 해석 불가, 기본값 사용", lineno, key, value)
    cfg.version = __version__  # 버전은 항상 코드 기준
    return cfg


def save_config(cfg: Config) -> None:
    lines = ["# key = value  (밥봇 JB 설정)"]
    for f in fields(Config):
        lines.append(f"{f.name} = {getattr(cfg, f.name)}")
    cfg.config_path().write_text("\n".join(lines) + "\n", encoding="utf-8-sig")
