from __future__ import annotations

from playwright.sync_api import Page, sync_playwright

from app.browser.cdp import connect_cdp
from app.core.config import get_settings


INPUT_SELECTOR = '.ql-editor[contenteditable="true"]'
SEND_SELECTOR = '#yuanbao-send-btn'

TEST_QUESTION = "请用一句话介绍腾讯元宝。"


def get_page() -> Page:
    raise NotImplementedError


def main() -> None:
    settings = get_settings()

    with sync_playwright() as playwright:
        browser = connect_cdp(
            playwright=playwright,
            cdp_url=settings.cdp_url,
        )

        if not browser.contexts:
            raise RuntimeError("没有找到浏览器 Context")

        context = browser.contexts[0]

        if not context.pages:
            raise RuntimeError("没有找到浏览器页面")

        page = context.pages[0]

        print("=" * 80)
        print("YUANBAO SEND SMOKE TEST")
        print("=" * 80)

        print(f"[TITLE] {page.title()}")
        print(f"[URL]   {page.url}")

        editor = page.locator(INPUT_SELECTOR).first

        if not editor.is_visible():
            raise RuntimeError("没有找到元宝输入框")

        print("[INPUT] 找到输入框")

        editor.click()
        editor.fill(TEST_QUESTION)

        print(f"[QUESTION] {TEST_QUESTION}")

        send_button = page.locator(SEND_SELECTOR).first

        send_button.wait_for(
            state="visible",
            timeout=5000,
        )

        print("[SEND] 找到发送按钮")

        send_button.click()

        print("[SEND] 已点击发送")

        page.wait_for_timeout(2000)

        print(f"[URL AFTER SEND] {page.url}")

        print()
        print("=" * 80)
        print("SEND STATUS: PASS")
        print("=" * 80)


if __name__ == "__main__":
    main()