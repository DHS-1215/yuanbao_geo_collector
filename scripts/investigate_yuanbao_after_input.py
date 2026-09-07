from __future__ import annotations

from playwright.sync_api import Locator, Page, sync_playwright

from app.browser.cdp import connect_cdp
from app.core.config import get_settings

TEST_QUESTION = "这是腾讯元宝 GEO 采集系统的输入测试，请不要发送。"


def print_element_info(locator: Locator, index: int) -> None:
    try:
        if not locator.is_visible():
            return

        info = locator.evaluate(
            """
            (el) => ({
                tag: el.tagName,
                text: (el.innerText || el.textContent || '').trim(),
                ariaLabel: el.getAttribute('aria-label'),
                title: el.getAttribute('title'),
                role: el.getAttribute('role'),
                type: el.getAttribute('type'),
                disabled: el.disabled ?? null,
                dataState: el.getAttribute('data-state'),
                dataTestId: el.getAttribute('data-testid'),
                className: typeof el.className === 'string'
                    ? el.className
                    : '',
                html: el.outerHTML,
            })
            """
        )

        text = info["text"]
        html = info["html"]
        class_name = info["className"]

        if len(text) > 150:
            text = text[:150] + "..."

        if len(html) > 500:
            html = html[:500] + "..."

        if len(class_name) > 200:
            class_name = class_name[:200] + "..."

        print("-" * 80)
        print(f"INDEX:       {index}")
        print(f"TAG:         {info['tag']}")
        print(f"TEXT:        {text!r}")
        print(f"ARIA-LABEL:  {info['ariaLabel']}")
        print(f"TITLE:       {info['title']}")
        print(f"ROLE:        {info['role']}")
        print(f"TYPE:        {info['type']}")
        print(f"DISABLED:    {info['disabled']}")
        print(f"DATA-STATE:  {info['dataState']}")
        print(f"DATA-TESTID: {info['dataTestId']}")
        print(f"CLASS:       {class_name!r}")
        print(f"HTML:        {html}")

    except Exception as exc:
        print(f"[WARN] index={index}: {exc}")


def inspect(page: Page, selector: str, title: str) -> None:
    print()
    print("=" * 80)
    print(title)
    print("=" * 80)

    locator = page.locator(selector)

    print(f"COUNT: {locator.count()}")

    for index in range(locator.count()):
        print_element_info(locator.nth(index), index)


def main() -> None:
    settings = get_settings()

    with sync_playwright() as playwright:
        browser = connect_cdp(
            playwright=playwright,
            cdp_url=settings.cdp_url,
        )

        context = browser.contexts[0]
        page = context.pages[0]

        print("=" * 80)
        print("YUANBAO AFTER INPUT INVESTIGATION")
        print("=" * 80)
        print(f"TITLE: {page.title()}")
        print(f"URL:   {page.url}")

        editor = page.locator('div[contenteditable="true"]').first

        if not editor.is_visible():
            raise RuntimeError("没有找到可见的元宝输入框")

        print()
        print("[EDITOR] 找到输入框")

        editor.click()
        editor.fill(TEST_QUESTION)

        print(f"[EDITOR] 已输入：{TEST_QUESTION}")
        print("[IMPORTANT] 本脚本不会发送问题")

        page.wait_for_timeout(1000)

        inspect(
            page,
            "button",
            "BUTTONS AFTER INPUT",
        )

        inspect(
            page,
            '[aria-label]',
            "ELEMENTS WITH ARIA-LABEL",
        )

        inspect(
            page,
            '[role="button"]',
            "ROLE=BUTTON AFTER INPUT",
        )

        print()
        print("=" * 80)
        print("INVESTIGATION COMPLETE - QUESTION NOT SENT")
        print("=" * 80)


if __name__ == "__main__":
    main()
