from __future__ import annotations

from playwright.sync_api import Page, sync_playwright

from app.browser.cdp import connect_cdp
from app.core.config import get_settings


def print_section(title: str) -> None:
    print()
    print("=" * 80)
    print(title)
    print("=" * 80)


def inspect_elements(
    page: Page,
    selector: str,
    title: str,
) -> None:
    print_section(title)

    locator = page.locator(selector)
    count = locator.count()

    print(f"COUNT: {count}")

    for index in range(count):
        element = locator.nth(index)

        try:
            if not element.is_visible():
                continue

            info = element.evaluate(
                """
                (el) => ({
                    tag: el.tagName,
                    text: (el.innerText || el.textContent || '').trim(),
                    placeholder: el.getAttribute('placeholder'),
                    ariaLabel: el.getAttribute('aria-label'),
                    role: el.getAttribute('role'),
                    type: el.getAttribute('type'),
                    contenteditable: el.getAttribute('contenteditable'),
                    className: typeof el.className === 'string'
                        ? el.className
                        : '',
                    id: el.id || '',
                    dataTestId: el.getAttribute('data-testid'),
                    dataRole: el.getAttribute('data-role'),
                    dataIndex: el.getAttribute('data-index'),
                })
                """
            )

            text = info.get("text") or ""

            # 防止整段聊天内容把终端刷爆
            if len(text) > 200:
                text = text[:200] + "..."

            class_name = info.get("className") or ""

            if len(class_name) > 200:
                class_name = class_name[:200] + "..."

            print("-" * 80)
            print(f"INDEX:           {index}")
            print(f"TAG:             {info.get('tag')}")
            print(f"ID:              {info.get('id')}")
            print(f"ROLE:            {info.get('role')}")
            print(f"TYPE:            {info.get('type')}")
            print(f"PLACEHOLDER:     {info.get('placeholder')}")
            print(f"ARIA-LABEL:      {info.get('ariaLabel')}")
            print(f"CONTENTEDITABLE: {info.get('contenteditable')}")
            print(f"DATA-TESTID:     {info.get('dataTestId')}")
            print(f"DATA-ROLE:       {info.get('dataRole')}")
            print(f"DATA-INDEX:      {info.get('dataIndex')}")
            print(f"TEXT:            {text!r}")
            print(f"CLASS:           {class_name!r}")

        except Exception as exc:
            print(f"[WARN] index={index}: {exc}")


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
        print("YUANBAO CONTROL INVESTIGATION")
        print("=" * 80)
        print(f"TITLE: {page.title()}")
        print(f"URL:   {page.url}")

        inspect_elements(
            page,
            "textarea",
            "TEXTAREA",
        )

        inspect_elements(
            page,
            "input",
            "INPUT",
        )

        inspect_elements(
            page,
            '[contenteditable="true"]',
            "CONTENTEDITABLE",
        )

        inspect_elements(
            page,
            "button",
            "BUTTON",
        )

        inspect_elements(
            page,
            '[role="button"]',
            "ROLE=BUTTON",
        )

        print()
        print("=" * 80)
        print("INVESTIGATION COMPLETE")
        print("=" * 80)


if __name__ == "__main__":
    main()