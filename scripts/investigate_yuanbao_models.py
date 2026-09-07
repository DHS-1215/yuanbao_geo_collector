from __future__ import annotations

from playwright.sync_api import Locator, Page, sync_playwright

from app.browser.cdp import connect_cdp
from app.core.config import get_settings
from app.yuanbao.selectors import (
    MODEL_MENU_SELECTOR,
    MODEL_SWITCH_SELECTOR,
)


def print_element(
    locator: Locator,
    index: int,
) -> None:
    try:
        if not locator.is_visible():
            return

        info = locator.evaluate(
            """
            (el) => {
                const attrs = {};

                for (const attr of el.attributes) {
                    if (
                        attr.name.startsWith('aria-')
                        || attr.name.startsWith('data-')
                    ) {
                        attrs[attr.name] = attr.value;
                    }
                }

                return {
                    tag: el.tagName,
                    text: (
                        el.innerText
                        || el.textContent
                        || ''
                    ).trim(),
                    id: el.id || '',
                    role: el.getAttribute('role'),
                    type: el.getAttribute('type'),
                    className:
                        typeof el.className === 'string'
                            ? el.className
                            : '',
                    attrs,
                };
            }
            """
        )

        text = info["text"] or ""
        class_name = info["className"] or ""

        if len(text) > 300:
            text = text[:300] + "..."

        if len(class_name) > 220:
            class_name = class_name[:220] + "..."

        print("-" * 100)
        print(f"INDEX: {index}")
        print(f"TAG:   {info['tag']}")
        print(f"ID:    {info['id']}")
        print(f"ROLE:  {info['role']}")
        print(f"TYPE:  {info['type']}")
        print(f"TEXT:  {text!r}")
        print(f"CLASS: {class_name!r}")

        print("ATTRS:")

        if info["attrs"]:
            for key, value in info["attrs"].items():
                print(
                    f"  {key} = {value!r}"
                )
        else:
            print("  <none>")

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


def open_mode_menu(page: Page) -> None:
    trigger = page.locator(
        MODEL_SWITCH_SELECTOR
    ).first

    trigger.wait_for(
        state="visible",
        timeout=5000,
    )

    if (
        trigger.get_attribute(
            "aria-expanded"
        )
        != "true"
    ):
        trigger.click()
        page.wait_for_timeout(300)


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
            "YUANBAO MODEL MENU INVESTIGATION"
        )
        print("=" * 100)

        print(f"[URL] {page.url}")

        open_mode_menu(page)

        model_entry = page.locator(
            MODEL_MENU_SELECTOR
        ).first

        model_entry.wait_for(
            state="visible",
            timeout=5000,
        )

        print(
            f"[MODEL ENTRY] "
            f"{model_entry.inner_text().strip()}"
        )

        print(
            f"[MODEL EXPANDED BEFORE] "
            f"{model_entry.get_attribute('aria-expanded')}"
        )

        model_entry.click()

        page.wait_for_timeout(500)

        print(
            f"[MODEL EXPANDED AFTER] "
            f"{model_entry.get_attribute('aria-expanded')}"
        )

        inspect(
            page,
            "button",
            "VISIBLE BUTTONS AFTER MODEL MENU",
        )

        inspect(
            page,
            '[role="menuitem"]',
            "ROLE MENUITEM",
        )

        inspect(
            page,
            '[role="menuitemradio"]',
            "ROLE MENUITEMRADIO",
        )

        inspect(
            page,
            '[role="option"]',
            "ROLE OPTION",
        )

        inspect(
            page,
            '[role="radio"]',
            "ROLE RADIO",
        )

        inspect(
            page,
            '[aria-checked]',
            "ARIA CHECKED",
        )

        inspect(
            page,
            '[aria-selected]',
            "ARIA SELECTED",
        )

        print()
        print("=" * 100)
        print(
            "MODEL INVESTIGATION COMPLETE"
        )
        print("=" * 100)

        print(
            "[IMPORTANT] "
            "只调查模型菜单，不主动切换模型"
        )


if __name__ == "__main__":
    main()