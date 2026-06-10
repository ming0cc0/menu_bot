"""밥봇 JB 엔트리포인트.

흐름: 단일 인스턴스 확인 → 데이터 준비 → 창 + 트레이 + 알림 스케줄러.
`--check`: GUI 없이 데이터/엔진 초기화만 검증하고 종료 (빌드 검증용).
"""
from __future__ import annotations

import logging
import sys

from . import recommender as rec
from .config import load_config
from .data_loader import ensure_sample_data, setup_error_log

log = logging.getLogger(__name__)


def run_check() -> int:
    cfg = load_config()
    first = ensure_sample_data(cfg.data_dir, cfg.personal_dir)
    from .data_loader import DataStore

    store = DataStore(cfg.data_dir, cfg.personal_dir)
    cands, _ = rec.collect_with_relaxation(store, rec.Query(cooldown_days=cfg.cooldown_days))
    print(f"OK first_run={first} restaurants={len(store.restaurants)} "
          f"menus={len(store.menus)} candidates={len(cands)} data_dir={cfg.data_dir}")
    return 0


def main() -> int:
    setup_error_log()
    if "--check" in sys.argv:
        return run_check()

    from . import singleinstance
    if not singleinstance.acquire():
        singleinstance.notify_existing()  # 기존 창을 띄우고 조용히 종료
        return 0

    cfg = load_config()
    first_run = ensure_sample_data(cfg.data_dir, cfg.personal_dir)

    from .notifier import NotifyScheduler
    from .tray import start_tray
    from .ui.app import MenuBotApp

    app = MenuBotApp(cfg, first_run=first_run)
    singleinstance.listen(lambda: app.post_event("show"))

    scheduler = NotifyScheduler(cfg)
    scheduler.start()

    tray_icon = start_tray(
        on_show=lambda: app.post_event("show"),
        on_spin=lambda: app.post_event("spin"),
        on_quit=lambda: app.post_event("quit"),
    )

    try:
        app.mainloop()
    finally:
        scheduler.stop()
        if tray_icon:
            tray_icon.stop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
