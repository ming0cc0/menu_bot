"""밥봇 JB 픽셀아트 에셋 생성기 (기획안 7-A).

색상·표정을 코드로 재생성/수정할 수 있다. 실행:
    python scripts/make_assets.py [출력폴더=assets]
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image

# ---- 컬러 팔레트 (기획안 7-A) -------------------------------------------
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


def grid_to_image(grid: list[str], overlays=(), shadow=False) -> Image.Image:
    h, w = len(grid), max(len(r) for r in grid)
    cells = [list(row.ljust(w, ".")) for row in grid]
    for x, y, ch in overlays:
        cells[y][x] = ch
    img = Image.new("RGBA", (w + (1 if shadow else 0), h + (1 if shadow else 0)), CLEAR)
    if shadow:  # 1px 우하단 그림자
        for y, row in enumerate(cells):
            for x, ch in enumerate(row):
                if ch != ".":
                    img.putpixel((x + 1, y + 1), TOMATO_SHADOW)
    for y, row in enumerate(cells):
        for x, ch in enumerate(row):
            if ch != ".":
                img.putpixel((x, y), PAL[ch])
    return img


def scale(img: Image.Image, factor: int) -> Image.Image:
    return img.resize((img.width * factor, img.height * factor), Image.NEAREST)


def mascot(expr: str) -> Image.Image:
    return grid_to_image(MASCOT_BASE, EXPRESSIONS[expr])


def logo() -> Image.Image:
    rows = [j + "." + b for j, b in zip(GLYPH_J, GLYPH_B)]
    return grid_to_image(rows, shadow=True)


def app_icon(size: int) -> Image.Image:
    """크림 배경 + 마스코트(기본 표정) 중앙 배치."""
    icon = Image.new("RGBA", (size, size), CREAM)
    m = mascot("base")
    factor = max(1, (size * 13 // 16) // m.width)
    m = scale(m, factor)
    icon.alpha_composite(m, ((size - m.width) // 2, (size - m.height) // 2))
    return icon


def main(out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    names = {"base": "jb_mascot.png", "hungry": "jb_mascot_hungry.png",
             "dizzy": "jb_mascot_dizzy.png", "happy": "jb_mascot_happy.png"}
    for expr, name in names.items():
        scale(mascot(expr), 8).save(out / name)          # 104x96
    scale(logo(), 6).save(out / "jb_logo.png")
    app_icon(256).save(out / "jb_app_icon_256.png")
    app_icon(32).save(out / "jb_tray_icon_32.png")
    app_icon(256).save(out / "jb.ico", sizes=[(16, 16), (32, 32), (48, 48), (256, 256)])
    print(f"OK: {len(list(out.glob('jb_*')))} assets -> {out}")


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent / "assets"
    main(target)
