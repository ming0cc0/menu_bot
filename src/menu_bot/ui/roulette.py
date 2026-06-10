"""룰렛 캔버스 위젯 — 가중 추출로 정해진 결과를 애니메이션으로 보여준다."""
from __future__ import annotations

import math
import tkinter as tk
from typing import Callable

from . import theme

SPIN_MS = 16            # 프레임 간격
SPIN_DURATION = 2.6     # 초
EXTRA_TURNS = 4         # 최소 회전 바퀴 수


class RouletteCanvas(tk.Canvas):
    def __init__(self, master, size: int = 320, **kw):
        super().__init__(master, width=size, height=size + 24,
                         bg=theme.CREAM, highlightthickness=0, **kw)
        self.size = size
        self.labels: list[str] = []
        self.offset = 0.0       # 휠 회전 각도(도)
        self.spinning = False
        self._after_id: str | None = None

    def set_candidates(self, labels: list[str]) -> None:
        self.labels = labels
        self.offset = 0.0
        self._draw()

    def _draw(self) -> None:
        self.delete("all")
        n = len(self.labels)
        cx, cy = self.size / 2, 12 + self.size / 2
        r = self.size / 2 - 8
        if n == 0:
            self.create_text(cx, cy, text="후보가 없어요", font=theme.FONT_BIG,
                             fill=theme.NORI)
            return
        seg = 360 / n
        for i, label in enumerate(self.labels):
            color = theme.WHEEL_COLORS[i % len(theme.WHEEL_COLORS)]
            start = (self.offset + i * seg) % 360
            self.create_arc(cx - r, cy - r, cx + r, cy + r, start=start,
                            extent=seg, fill=color, outline=theme.CREAM, width=2)
            mid = math.radians(start + seg / 2)
            tx = cx + math.cos(mid) * r * 0.62
            ty = cy - math.sin(mid) * r * 0.62
            text = label if len(label) <= 6 else label[:5] + "…"
            self.create_text(tx, ty, text=text, font=theme.FONT_BOLD,
                             fill=theme.NORI if color in (theme.SPARK, theme.BLUSH)
                             else theme.WHITE)
        # 중심 캡 + 상단 포인터
        self.create_oval(cx - 18, cy - 18, cx + 18, cy + 18,
                         fill=theme.WHITE, outline=theme.RICE_EDGE, width=3)
        self.create_polygon(cx - 12, 2, cx + 12, 2, cx, 26,
                            fill=theme.TOMATO, outline=theme.TOMATO_SHADOW, width=2)

    def spin_to(self, index: int, on_done: Callable[[], None]) -> None:
        """index 칸이 포인터(상단 90도)에 멈추도록 회전."""
        if self.spinning or not self.labels:
            return
        n = len(self.labels)
        seg = 360 / n
        # 목표: offset + (index+0.5)*seg ≡ 90 (mod 360)
        target_mod = (90 - (index + 0.5) * seg) % 360
        delta = (target_mod - self.offset) % 360 + EXTRA_TURNS * 360
        start_offset = self.offset
        frames = int(SPIN_DURATION * 1000 / SPIN_MS)
        self.spinning = True

        def step(frame: int = 0) -> None:
            t = frame / frames
            eased = 1 - (1 - t) ** 3  # ease-out cubic
            self.offset = (start_offset + delta * eased) % 360
            self._draw()
            if frame < frames:
                self._after_id = self.after(SPIN_MS, step, frame + 1)
            else:
                self.spinning = False
                self._after_id = None
                on_done()

        step()

    def stop(self) -> None:
        if self._after_id:
            self.after_cancel(self._after_id)
            self._after_id = None
        self.spinning = False
