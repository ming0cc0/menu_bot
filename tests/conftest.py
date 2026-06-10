from __future__ import annotations

from pathlib import Path

import pytest

from menu_bot.data_loader import ENCODING, DataStore

RESTAURANTS = """\
# 이름 | 카테고리 | 도보분 | 가격대 | 인원수용 | 태그 | 비올때OK
가까운한식 | 한식 | 3 | 1 | 4 | 빠름 | Y
먼일식 | 일식 | 15 | 3 | 8 | 초밥 | N
회식고기집 | 한식 | 12 | 3 | 30 | 회식,단체석 | N
중간중식 | 중식 | 8 | 2 | 12 | 단체 | Y
"""

MENUS = """\
# 메뉴 | 카테고리 | 맵기
김치찌개 | 한식 | 2
마라탕 | 중식 | 3
돈카츠 | 일식 | 0
"""


def write(path: Path, text: str) -> Path:
    path.write_text(text, encoding=ENCODING)
    return path


@pytest.fixture
def data_dir(tmp_path: Path) -> Path:
    write(tmp_path / "restaurants.txt", RESTAURANTS)
    write(tmp_path / "menus.txt", MENUS)
    write(tmp_path / "suggestions.txt", "# 등록일 | 등록자 | 이름 | 카테고리 | 한줄평\n")
    write(tmp_path / "history.txt", "# 날짜 | 모드 | 선택결과\n")
    return tmp_path


@pytest.fixture
def store(data_dir: Path) -> DataStore:
    return DataStore(data_dir)
