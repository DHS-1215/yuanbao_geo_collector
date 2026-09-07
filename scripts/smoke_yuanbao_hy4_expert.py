from playwright.sync_api import sync_playwright

from app.browser.cdp import connect_cdp
from app.core.config import get_settings
from app.yuanbao.client import YuanbaoClient
from app.yuanbao.types import (
    YuanbaoMode,
    YuanbaoModel,
)

QUESTION = "请只回答：Hy4专家模式采集成功"


def main() -> None:
    settings = get_settings()

    with sync_playwright() as playwright:
        browser = connect_cdp(
            playwright=playwright,
            cdp_url=settings.cdp_url,
        )

        page = browser.contexts[0].pages[0]

        client = YuanbaoClient(
            page=page,
            answer_timeout_seconds=180,
        )

        print("=" * 80)
        print("YUANBAO HY4 EXPERT SMOKE TEST")
        print("=" * 80)

        client.new_chat()

        client.set_profile(
            model=YuanbaoModel.HY4_PREVIEW,
            mode=YuanbaoMode.EXPERT,
        )

        print("[PROFILE] Hy4 preview + 专家模式")
        print(f"[QUESTION] {QUESTION}")

        answer = client.ask(QUESTION)

        print(f"[ANSWER] {answer}")
        print(f"[URL] {page.url}")

        print()
        print("=" * 80)
        print("HY4 EXPERT STATUS: PASS")
        print("=" * 80)


if __name__ == "__main__":
    main()
