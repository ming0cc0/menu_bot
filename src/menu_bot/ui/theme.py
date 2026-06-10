"""디자인 토큰 + 에셋 로더 — "Midnight Bento × Pixel Soul" (UI개편_기획안_v2 3장).

다크 단일 모드 고정. 모든 색은 단일 hex 문자열 — tk.Canvas와 토큰을 공유한다.
"""
from __future__ import annotations

import tkinter as tk

import customtkinter as ctk
from PIL import Image

from ..paths import resource_path

# ---- 표면 (휘도 단계 = 다크의 그림자) ------------------------------------
BG_BASE = "#101216"
BG_SIDEBAR = "#15181D"
BG_CARD = "#1C2027"
BG_ELEV = "#242933"
BG_HOVER = "#2C323E"

# ---- 보더 ----------------------------------------------------------------
BORDER = "#2E3440"
BORDER_GLOW = "#5A3528"   # 토마토 틴트 — 활성/호버 "글래스" 모사

# ---- 텍스트 ---------------------------------------------------------------
TEXT_HI = "#F4F1E8"       # v1 크림 계승
TEXT_MID = "#A9ADB6"
TEXT_DIM = "#6E7480"

# ---- 포인트 ---------------------------------------------------------------
TOMATO = "#E8552E"
TOMATO_HOVER = "#FF6B3D"
TOMATO_PRESS = "#C4441F"
TOMATO_SOFT = "#33201A"

GLOW_STEPS = ["#3A2018", "#6B3220", "#A8441F", "#E8552E"]

SUCCESS = "#7FB069"
WARN = "#FFD166"

# 룰렛 칸 8색 (다크 친화 — 라벨 텍스트 병기로 색상 단독 구분 금지)
WHEEL_COLORS = ["#D94F2B", "#D9A441", "#6FA05E", "#4FA3A1",
                "#C66E84", "#8E6FC4", "#C77F3F", "#5E8E89"]

FONT_FAMILY = "Malgun Gothic"
RADIUS_CARD = 14
RADIUS_PILL = 999

_fonts: dict[tuple, ctk.CTkFont] = {}
_images: dict[str, tk.PhotoImage] = {}
_ctk_images: dict[tuple, ctk.CTkImage] = {}

MASCOT_DARK = {
    "base": "jb_mascot_dark.png",
    "blink": "jb_mascot_blink_dark.png",
    "hungry": "jb_mascot_hungry_dark.png",
    "dizzy": "jb_mascot_dizzy_dark.png",
    "happy": "jb_mascot_happy_dark.png",
}


def init_appearance() -> None:
    """루트 생성 전에 호출 — 시작 시 흰 창 플래시 방지."""
    ctk.set_appearance_mode("dark")


def font(size: int = 11, bold: bool = False) -> ctk.CTkFont:
    key = (size, bold)
    if key not in _fonts:
        _fonts[key] = ctk.CTkFont(family=FONT_FAMILY, size=size,
                                  weight="bold" if bold else "normal")
    return _fonts[key]


def image(name: str, zoom: int = 1) -> tk.PhotoImage | None:
    """tk.PhotoImage 로더 (Canvas·iconphoto용). 정수배 확대."""
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


def ctk_image(name: str, height: int) -> ctk.CTkImage | None:
    """CTkImage 로더 — CTk의 자동 리샘플(LANCZOS)이 픽셀아트를 뭉개므로
    PIL NEAREST로 사전 정수배 확대한 뒤 동일 size를 지정한다."""
    key = (name, height)
    if key in _ctk_images:
        return _ctk_images[key]
    path = resource_path(f"assets/{name}")
    if not path.exists():
        return None
    pil = Image.open(path)
    if height >= pil.height:  # 정수배 확대
        factor = max(1, round(height / pil.height))
        pil = pil.resize((pil.width * factor, pil.height * factor), Image.NEAREST)
    else:                     # 정수 분할 축소 (픽셀 균일 유지)
        sub = max(1, round(pil.height / height))
        pil = pil.resize((max(1, pil.width // sub), max(1, pil.height // sub)),
                         Image.NEAREST)
    img = ctk.CTkImage(light_image=pil, dark_image=pil, size=pil.size)
    _ctk_images[key] = img
    return img


def mascot(expr: str, height: int = 96) -> ctk.CTkImage | None:
    """다크 네온 마스코트 (표정: base/blink/hungry/dizzy/happy)."""
    return ctk_image(MASCOT_DARK.get(expr, MASCOT_DARK["base"]), height)


def text_on(bg_hex: str) -> str:
    """배경 휘도에 따라 가독 텍스트 색 선택 (룰렛 칸 라벨용)."""
    r, g, b = (int(bg_hex[i:i + 2], 16) for i in (1, 3, 5))
    luminance = 0.299 * r + 0.587 * g + 0.114 * b
    return "#1A1B1E" if luminance > 150 else TEXT_HI


def brighten(hex_color: str, factor: float) -> str:
    """틱 하이라이트·펄스용 색 밝힘."""
    r, g, b = (min(255, int(int(hex_color[i:i + 2], 16) * factor))
               for i in (1, 3, 5))
    return f"#{r:02x}{g:02x}{b:02x}"
