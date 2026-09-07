from __future__ import annotations

from playwright.sync_api import Locator, Page, sync_playwright

from app.browser.cdp import connect_cdp
from app.core.config import get_settings
from app.yuanbao.selectors import MODEL_SWITCH_SELECTOR


def print_element(
    locator: Locator,
    index: int,
) -> None:
    try:
        if not locator.is_visible():
            return

        info = locator.evaluate(
            """
            (el) => ({
                tag: el.tagName,
                text: (
                    el.innerText
                    || el.textContent
                    || ''
                ).trim(),
                id: el.id || '',
                role: el.getAttribute('role'),
                ariaLabel: el.getAttribute('aria-label'),
                ariaExpanded: el.getAttribute('aria-expanded'),
                ariaSelected: el.getAttribute('aria-selected'),
                ariaChecked: el.getAttribute('aria-checked'),
                dataState: el.getAttribute('data-state'),
                dataValue: el.getAttribute('data-value'),
                dataMode: el.getAttribute('data-mode'),
                className:
                    typeof el.className === 'string'
                        ? el.className
                        : '',
            })
            """
        )

        text = info["text"] or ""
        class_name = info["className"] or ""

        if len(text) > 300:
            text = text[:300] + "..."

        if len(class_name) > 250:
            class_name = class_name[:250] + "..."

        print("-" * 100)
        print(f"INDEX:         {index}")
        print(f"TAG:           {info['tag']}")
        print(f"ID:            {info['id']}")
        print(f"ROLE:          {info['role']}")
        print(f"ARIA-LABEL:    {info['ariaLabel']}")
        print(f"ARIA-EXPANDED: {info['ariaExpanded']}")
        print(f"ARIA-SELECTED: {info['ariaSelected']}")
        print(f"ARIA-CHECKED:  {info['ariaChecked']}")
        print(f"DATA-STATE:    {info['dataState']}")
        print(f"DATA-VALUE:    {info['dataValue']}")
        print(f"DATA-MODE:     {info['dataMode']}")
        print(f"CLASS:         {class_name!r}")
        print(f"TEXT:          {text!r}")

    except Exception as exc:
        print(
            f"[WARN] index={index}: {exc}"
        )


def inspect(
    page: Page,
    selector: str,
    title: str,
) -> None:
    print()
    print("=" * 100)
    print(title)
    print("=" * 100)

    locator = page.locator(selector)

    print(f"COUNT: {locator.count()}")

    for index in range(locator.count()):
        print_element(
            locator.nth(index),
            index,
        )


def main() -> None:
    settings = get_settings()

    with sync_playwright() as playwright:
        browser = connect_cdp(
            playwright=playwright,
            cdp_url=settings.cdp_url,
        )

        if not browser.contexts:
            raise RuntimeError(
                "没有找到浏览器 Context"
            )

        context = browser.contexts[0]

        if not context.pages:
            raise RuntimeError(
                "没有找到浏览器页面"
            )

        page = context.pages[0]

        print("=" * 100)
        print(
            "YUANBAO MODE MENU INVESTIGATION"
        )
        print("=" * 100)

        print(f"[URL] {page.url}")

        trigger = page.locator(
            MODEL_SWITCH_SELECTOR
        ).first

        trigger.wait_for(
            state="visible",
            timeout=5000,
        )

        print(
            f"[CURRENT MODE] "
            f"{trigger.inner_text().strip()}"
        )

        print(
            f"[BEFORE EXPANDED] "
            f"{trigger.get_attribute('aria-expanded')}"
        )

        trigger.click()

        page.wait_for_timeout(500)

        print(
            f"[AFTER EXPANDED] "
            f"{trigger.get_attribute('aria-expanded')}"
        )

        inspect(
            page,
            "button",
            "VISIBLE BUTTONS",
        )

        inspect(
            page,
            '[role="option"]',
            "ROLE OPTION",
        )

        inspect(
            page,
            '[role="menuitem"]',
            "ROLE MENUITEM",
        )

        inspect(
            page,
            '[role="radio"]',
            "ROLE RADIO",
        )

        inspect(
            page,
            '[aria-selected]',
            "ARIA SELECTED",
        )

        inspect(
            page,
            '[aria-checked]',
            "ARIA CHECKED",
        )

        inspect(
            page,
            '[data-state]',
            "DATA STATE",
        )

        print()
        print("=" * 100)
        print(
            "MODE INVESTIGATION COMPLETE"
        )
        print("=" * 100)

        print(
            "[IMPORTANT] "
            "本脚本只打开模式菜单，"
            "不会主动切换模式"
        )


if __name__ == "__main__":
    main()