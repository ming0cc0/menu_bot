"""밥봇 JB 픽셀아트 에셋 생성기 (UI개편_기획안_v2 4장).

라이트(v1: 아이콘·트레이용) + 다크 네온(v2 UI용) 에셋을 모두 생성한다. 실행:
    python scripts/make_assets.py [출력폴더=assets]
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image

# ---- 컬러 팔레트 (v1 기획안 7-A) ----------------------------------------
TOMATO = (232, 85, 46, 255)        # E8552E 메인/JB
TOMATO_SHADOW = (168, 51, 26, 255) # A8331A
CREAM = (255, 246, 224, 255)       # FFF6E0 배경
NORI = (51, 64, 47, 255)           # 33402F 김
RICE = (255, 255, 255, 255)        # FFFFFF 쌀밥
RICE_EDGE = (214, 205, 184, 255)   # D6CDB8 외곽
BLUSH = (255, 159, 176, 255)       # FF9FB0 볼터치
SPARK = (255, 209, 102, 255)       # FFD166 반짝
CLEAR = (0, 0, 0, 0)

PAL = {".": CLEAR, "o": RICE_EDGE, "w": RICE, "n": NORI, "k": NORI,
       "b": BLUSH, "s": SPARK, "m": TOMATO_SHADOW, "t": TOMATO}

# ---- 다크 네온 변형 (v2 기획안 3.2/4장) ----------------------------------
NORI_DARK = (62, 77, 57, 255)       # 3E4D39 — 다크 배경에 묻힘 방지
RICE_EDGE_DARK = (237, 230, 212, 255)  # EDE6D4 — 외곽선 밝힘
PAL_DARK = {**PAL, "o": RICE_EDGE_DARK, "n": NORI_DARK, "k": NORI_DARK}

GLOW1 = (255, 107, 61, 150)   # TOMATO_HOVER, 1차 글로우 링
GLOW2 = (232, 85, 46, 60)     # TOMATO, 2차 글로우 링

# ---- 마스코트: 13x12 셀 오니기리 ----------------------------------------
MASCOT_BASE = [
    ".....ooo.....",
    "....owwwo....",
    "...owwwwwo...",
    "...owwwwwo...",
    "..owwwwwwwo..",
    "..owwwwwwwo..",
    ".owwwwwwwwwo.",
    ".owwwwwwwwwo.",
    "owwwwwwwwwwwo",
    "ownnnnnnnnnwo",
    ".onnnnnnnnno.",
    "..ooooooooo..",
]

# 표정 오버레이: (x, y, 팔레트문자)
EXPRESSIONS = {
    "base": [
        (4, 5, "k"), (8, 5, "k"),            # 눈
        (6, 7, "k"),                          # 입
        (2, 6, "b"), (10, 6, "b"),            # 볼터치
    ],
    "blink": [                                 # 아이들 깜빡임 (v2)
        (3, 5, "k"), (4, 5, "k"), (5, 5, "k"),
        (7, 5, "k"), (8, 5, "k"), (9, 5, "k"),
        (6, 7, "k"),
        (2, 6, "b"), (10, 6, "b"),
    ],
    "hungry": [
        (4, 5, "k"), (8, 5, "k"),
        (5, 7, "n"), (6, 7, "m"), (7, 7, "n"),  # 벌린 입
        (5, 8, "n"), (6, 8, "m"), (7, 8, "n"),
        (2, 6, "b"), (10, 6, "b"),
    ],
    "dizzy": [                                 # 고민중: 눈 ×
        (3, 4, "k"), (5, 4, "k"), (4, 5, "k"), (3, 6, "k"), (5, 6, "k"),
        (7, 4, "k"), (9, 4, "k"), (8, 5, "k"), (7, 6, "k"), (9, 6, "k"),
        (6, 8, "k"),
    ],
    "happy": [                                 # 당첨!: 웃는 눈 ^^ + 반짝
        (3, 5, "k"), (4, 4, "k"), (5, 5, "k"),
        (7, 5, "k"), (8, 4, "k"), (9, 5, "k"),
        (5, 7, "k"), (6, 8, "k"), (7, 7, "k"),  # 웃는 입
        (2, 6, "b"), (10, 6, "b"),
        (0, 1, "s"), (12, 2, "s"), (1, 9, "s"),
    ],
}

# ---- JB 로고 (5x7 픽셀 폰트) --------------------------------------------
GLYPH_J = ["ttttt", "...t.", "...t.", "...t.", "t..t.", "t..t.", ".tt.."]
GLYPH_B = ["tttt.", "t...t", "t...t", "tttt.", "t...t", "t...t", "tttt."]


def grid_to_image(grid: list[str], overlays=(), shadow=False,
                  pal: dict | None = None, padding: int = 0) -> Image.Image:
    pal = pal or PAL
    h, w = len(grid), max(len(r) for r in grid)
    cells = [list(row.ljust(w, ".")) for row in grid]
    for x, y, ch in overlays:
        cells[y][x] = ch
    extra = 1 if shadow else 0
    img = Image.new("RGBA", (w + extra + padding * 2, h + extra + padding * 2), CLEAR)
    if shadow:  # 1px 우하단 그림자 (라이트용)
        for y, row in enumerate(cells):
            for x, ch in enumerate(row):
                if ch != ".":
                    img.putpixel((x + 1 + padding, y + 1 + padding), TOMATO_SHADOW)
    for y, row in enumerate(cells):
        for x, ch in enumerate(row):
            if ch != ".":
                img.putpixel((x + padding, y + padding), pal[ch])
    return img


def add_glow(img: Image.Image) -> Image.Image:
    """불투명 픽셀 주변 투명 셀에 2단계 토마토 글로우 링 (다크 네온 모사).

    픽셀아트 문법(정수 셀)을 지키며 블러 없이 발광 효과를 낸다.
    이미지에 최소 2px 패딩이 있어야 한다.
    """
    def neighbors(x: int, y: int):
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < img.width and 0 <= ny < img.height:
                yield nx, ny

    px = img.load()
    solid = {(x, y) for y in range(img.height) for x in range(img.width)
             if px[x, y][3] > 200}
    ring1 = set()
    for x, y in solid:
        for nx, ny in neighbors(x, y):
            if px[nx, ny][3] == 0:
                ring1.add((nx, ny))
    for x, y in ring1:
        px[x, y] = GLOW1
    ring2 = set()
    for x, y in ring1:
        for nx, ny in neighbors(x, y):
            if px[nx, ny][3] == 0:
                ring2.add((nx, ny))
    for x, y in ring2:
        px[x, y] = GLOW2
    return img


def scale(img: Image.Image, factor: int) -> Image.Image:
    return img.resize((img.width * factor, img.height * factor), Image.NEAREST)


def mascot(expr: str, dark: bool = False) -> Image.Image:
    if dark:
        img = grid_to_image(MASCOT_BASE, EXPRESSIONS[expr], pal=PAL_DARK, padding=2)
        return add_glow(img)
    return grid_to_image(MASCOT_BASE, EXPRESSIONS[expr])


def logo(dark: bool = False) -> Image.Image:
    rows = [j + "." + b for j, b in zip(GLYPH_J, GLYPH_B)]
    if dark:
        return add_glow(grid_to_image(rows, padding=2))
    return grid_to_image(rows, shadow=True)


def app_icon(size: int) -> Image.Image:
    """크림 배경 + 마스코트(기본 표정) 중앙 배치 (라이트 — 아이콘/트레이용)."""
    icon = Image.new("RGBA", (size, size), CREAM)
    m = mascot("base")
    factor = max(1, (size * 13 // 16) // m.width)
    m = scale(m, factor)
    icon.alpha_composite(m, ((size - m.width) // 2, (size - m.height) // 2))
    return icon


def main(out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    light_names = {"base": "jb_mascot.png", "hungry": "jb_mascot_hungry.png",
                   "dizzy": "jb_mascot_dizzy.png", "happy": "jb_mascot_happy.png"}
    for expr, name in light_names.items():
        scale(mascot(expr), 8).save(out / name)
    # 다크 네온 변형 (v2 UI) — 깜빡임 프레임 포함
    dark_names = {"base": "jb_mascot_dark.png", "blink": "jb_mascot_blink_dark.png",
                  "hungry": "jb_mascot_hungry_dark.png",
                  "dizzy": "jb_mascot_dizzy_dark.png",
                  "happy": "jb_mascot_happy_dark.png"}
    for expr, name in dark_names.items():
        scale(mascot(expr, dark=True), 8).save(out / name)
    scale(logo(), 6).save(out / "jb_logo.png")
    scale(logo(dark=True), 6).save(out / "jb_logo_dark.png")
    app_icon(256).save(out / "jb_app_icon_256.png")
    app_icon(32).save(out / "jb_tray_icon_32.png")
    app_icon(256).save(out / "jb.ico", sizes=[(16, 16), (32, 32), (48, 48), (256, 256)])
    print(f"OK: {len(list(out.glob('jb_*')))} assets -> {out}")


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent / "assets"
    main(target)
