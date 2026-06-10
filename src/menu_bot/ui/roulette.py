"""히어로 룰렛 캔버스 (기획안 v2 4장-3).

네온 글로우 링 + 와인드업 → quintic ease-out 본회전 + 틱 하이라이트
+ 당첨 펄스 3회 + 컨페티 50파티클. 결과는 추천 엔진이 미리 정한다.
"""
from __future__ import annotations

import math
import random
import tkinter as tk
from typing import Callable

from . import theme

SPIN_MS = 16
WINDUP_MS = 150
WINDUP_DEG = -8
SPIN_DURATION = 2.6
EXTRA_TURNS = 4
PULSE_COUNT = 3
PULSE_MS = 120
CONFETTI_N = 50
CONFETTI_MS = 33
CONFETTI_FRAMES = 36  # ~1.2초


class RouletteCanvas(tk.Canvas):
    def __init__(self, master, size: int = 320, **kw):
        super().__init__(master, width=size, height=size + 28,
                         bg=theme.BG_CARD, highlightthickness=0, **kw)
        self.size = size
        self.labels: list[str] = []
        self.offset = 0.0
        self.spinning = False
        self._after_ids: set[str] = set()
        self._highlight_idx: int | None = None
        self._pulse_bright = False
        self._confetti: list[dict] = []
        hub = theme.image("jb_mascot_dark.png")
        self._hub_img = hub.subsample(3, 3) if hub else None

    # ------------------------------------------------------------ after 관리
    def _later(self, ms: int, fn, *args) -> None:
        aid = self.after(ms, lambda: (self._after_ids.discard(aid), fn(*args))[-1])
        self._after_ids.add(aid)

    def stop(self) -> None:
        """진행 중인 모든 연출(스핀·펄스·컨페티) 취소."""
        for aid in list(self._after_ids):
            try:
                self.after_cancel(aid)
            except ValueError:
                pass
        self._after_ids.clear()
        self.spinning = False
        self._confetti = []
        self._highlight_idx = None

    # ------------------------------------------------------------ 그리기
    def set_candidates(self, labels: list[str]) -> None:
        self.labels = labels
        self.offset = 0.0
        self._highlight_idx = None
        self._draw()

    def _pointer_index(self) -> int | None:
        """포인터(상단 90°) 아래 칸 인덱스."""
        if not self.labels:
            return None
        seg = 360 / len(self.labels)
        return int(((90 - self.offset) % 360) // seg)

    def _draw(self) -> None:
        self.delete("all")
        n = len(self.labels)
        cx, cy = self.size / 2, 16 + self.size / 2
        r = self.size / 2 - 14
        # 네온 글로우 동심원 링 (안쪽으로 갈수록 밝게)
        pulse = self.spinning and (int(self.offset) // 30) % 2 == 0
        for i, color in enumerate(theme.GLOW_STEPS):
            ring_r = r + 12 - i * 3
            width = 5 - i
            if i == len(theme.GLOW_STEPS) - 1 and pulse:
                color = theme.TOMATO_HOVER  # 회전 중 맥동
            self.create_oval(cx - ring_r, cy - ring_r, cx + ring_r, cy + ring_r,
                             outline=color, width=max(width, 1))
        if n == 0:
            # 빈 상태: 고스트 휠
            self.create_oval(cx - r, cy - r, cx + r, cy + r,
                             fill=theme.BG_ELEV, outline=theme.BORDER, width=2)
            self.create_text(cx, cy, text="후보가 없어요", font=(theme.FONT_FAMILY, 13, "bold"),
                             fill=theme.TEXT_DIM)
            return
        seg = 360 / n
        tick_idx = self._pointer_index() if self.spinning else None
        for i, label in enumerate(self.labels):
            color = theme.WHEEL_COLORS[i % len(theme.WHEEL_COLORS)]
            if i == tick_idx:
                color = theme.brighten(color, 1.25)          # 틱 하이라이트
            if i == self._highlight_idx and self._pulse_bright:
                color = theme.brighten(color, 1.45)          # 당첨 펄스
            start = (self.offset + i * seg) % 360
            self.create_arc(cx - r, cy - r, cx + r, cy + r, start=start,
                            extent=seg, fill=color, outline=theme.BG_CARD, width=3)
            mid = math.radians(start + seg / 2)
            tx = cx + math.cos(mid) * r * 0.63
            ty = cy - math.sin(mid) * r * 0.63
            text = label if len(label) <= 6 else label[:5] + "…"
            self.create_text(tx, ty, text=text, font=(theme.FONT_FAMILY, 10, "bold"),
                             fill=theme.text_on(color))
        # 허브: 다크 원 + 토마토 링 + 미니 마스코트
        self.create_oval(cx - 26, cy - 26, cx + 26, cy + 26,
                         fill=theme.BG_ELEV, outline=theme.TOMATO, width=2)
        if self._hub_img:
            self.create_image(cx, cy, image=self._hub_img)
        # 네온 포인터 (글로우 외곽 + 토마토 본체)
        self.create_polygon(cx - 15, 2, cx + 15, 2, cx, 32,
                            fill=theme.GLOW_STEPS[1], outline="")
        self.create_polygon(cx - 11, 4, cx + 11, 4, cx, 28,
                            fill=theme.TOMATO_HOVER, outline=theme.TOMATO_PRESS,
                            width=1)
        # 컨페티 파티클
        for p in self._confetti:
            self.create_rectangle(p["x"], p["y"], p["x"] + p["size"],
                                  p["y"] + p["size"], fill=p["color"], outline="")

    # ------------------------------------------------------------ 스핀
    def spin_to(self, index: int, on_done: Callable[[], None]) -> None:
        """와인드업 → quintic 본회전 → 당첨 펄스+컨페티. index 칸이 포인터에 멈춤."""
        if self.spinning or not self.labels:
            return
        self.spinning = True
        self._highlight_idx = None
        start_offset = self.offset
        windup_frames = max(1, WINDUP_MS // SPIN_MS)

        def windup(frame: int = 1) -> None:
            t = frame / windup_frames
            self.offset = (start_offset + WINDUP_DEG * t) % 360
            self._draw()
            if frame < windup_frames:
                self._later(SPIN_MS, windup, frame + 1)
            else:
                main_spin()

        def main_spin() -> None:
            n = len(self.labels)
            seg = 360 / n
            base = self.offset
            target_mod = (90 - (index + 0.5) * seg) % 360
            delta = (target_mod - base) % 360 + EXTRA_TURNS * 360
            frames = int(SPIN_DURATION * 1000 / SPIN_MS)

            def step(frame: int = 1) -> None:
                t = frame / frames
                eased = 1 - (1 - t) ** 5  # quintic ease-out
                self.offset = (base + delta * eased) % 360
                self._draw()
                if frame < frames:
                    self._later(SPIN_MS, step, frame + 1)
                else:
                    self.spinning = False
                    self._highlight_idx = index
                    self._start_pulse()
                    self._start_confetti()
                    on_done()

            step()

        windup()

    # ------------------------------------------------------------ 당첨 연출
    def _start_pulse(self, count: int = PULSE_COUNT * 2) -> None:
        if count <= 0:
            self._pulse_bright = False
            self._draw()
            return
        self._pulse_bright = not self._pulse_bright
        self._draw()
        self._later(PULSE_MS, self._start_pulse, count - 1)

    def _start_confetti(self) -> None:
        cx = self.size / 2
        self._confetti = [{
            "x": cx + random.uniform(-30, 30),
            "y": 20 + random.uniform(-10, 10),
            "vx": random.uniform(-3.2, 3.2),
            "vy": random.uniform(-4.5, -1.0),
            "size": random.randint(3, 6),
            "color": random.choice(theme.WHEEL_COLORS + [theme.WARN, theme.TOMATO_HOVER]),
        } for _ in range(CONFETTI_N)]

        def tick(frame: int = 0) -> None:
            for p in self._confetti:
                p["vy"] += 0.35          # 중력
                p["vx"] *= 0.99          # 드리프트 감쇠
                p["x"] += p["vx"]
                p["y"] += p["vy"]
            if frame >= CONFETTI_FRAMES:
                self._confetti = []
            self._draw()
            if frame < CONFETTI_FRAMES:
                self._later(CONFETTI_MS, tick, frame + 1)

        tick()
