"""데이터 모델 (txt 한 줄 = 객체 하나)."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Restaurant:
    name: str
    category: str = "기타"
    walk_min: int = 10
    price: int = 2          # 1~3
    capacity: int = 4
    tags: list[str] = field(default_factory=list)
    rain_ok: bool = False
    source: str = "master"  # master | suggestion

    @property
    def display(self) -> str:
        return f"{self.name} ({self.category}·도보 {self.walk_min}분)"


@dataclass
class MenuItem:
    name: str
    category: str = "기타"
    spice: int = 0          # 0~3

    @property
    def display(self) -> str:
        return f"{self.name} ({self.category})"


@dataclass
class Suggestion:
    date: str
    author: str
    name: str
    category: str
    comment: str = ""


@dataclass
class HistoryEntry:
    date: str               # YYYY-MM-DD
    mode: str               # 점심 | 저녁 | 회식 | 메뉴
    choice: str
