"""비주얼 아이덴티티 (기획안 7-A): 팔레트, 폰트, 픽셀 에셋 로더."""
from __future__ import annotations

import tkinter as tk

from ..paths import resource_path

TOMATO = "#E8552E"
TOMATO_SHADOW = "#A8331A"
CREAM = "#FFF6E0"
NORI = "#33402F"
RICE_EDGE = "#D6CDB8"
BLUSH = "#FF9FB0"
SPARK = "#FFD166"
WHITE = "#FFFFFF"

# 룰렛 칸 색상 순환 (색상만으로 구분하지 않도록 라벨 텍스트 병기 — 접근성)
WHEEL_COLORS = [TOMATO, SPARK, "#7FB069", "#5BC0BE", BLUSH, "#B388EB",
                "#F4A259", "#9BC1BC"]

FONT = ("Malgun Gothic", 10)
FONT_BOLD = ("Malgun Gothic", 10, "bold")
FONT_BIG = ("Malgun Gothic", 14, "bold")
FONT_TITLE = ("Malgun Gothic", 12, "bold")

_images: dict[str, tk.PhotoImage] = {}


def image(name: str, zoom: int = 1) -> tk.PhotoImage | None:
    """assets/ PNG 로더. 정수배 확대(Nearest)로 픽셀 선명도 유지. 없으면 None."""
    key = f"{name}@{zoom}"
    if key in _images:
        return _images[key]
    path = resource_path(f"assets/{name}")
    if not path.exists():
        return None
    img = tk.PhotoImage(file=str(path))
    if zoom > 1:
        img = img.zoom(zoom, zoom)
    _images[key] = img  # GC 방지 캐시
    return img
