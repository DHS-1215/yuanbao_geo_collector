from __future__ import annotations

from playwright.sync_api import Page, sync_playwright

from app.browser.cdp import connect_cdp
from app.core.config import get_settings
from app.yuanbao.selectors import MODEL_SWITCH_SELECTOR

MODES = [
    "快速回答",
    "深度思考",
    "专家模式",
    "快速回答",
]


def open_mode_menu(page: Page) -> None:
    trigger = page.locator(
        MODEL_SWITCH_SELECTOR
    ).first

    trigger.wait_for(
        state="visible",
        timeout=5000,
    )

    expanded = trigger.get_attribute(
        "aria-expanded"
    )

    if expanded != "true":
        trigger.click()
        page.wait_for_timeout(300)


def get_selected_mode(page: Page) -> str | None:
    options = page.locator(
        'button[role="menuitemradio"]'
    )

    for index in range(options.count()):
        option = options.nth(index)

        if (
                option.get_attribute("aria-checked")
                == "true"
        ):
            text = option.inner_text().strip()

            if text:
                return text.splitlines()[0]

    return None


def select_mode(
        page: Page,
        mode_name: str,
) -> None:
    open_mode_menu(page)

    option = (
        page.locator(
            'button[role="menuitemradio"]'
        )
        .filter(has_text=mode_name)
        .first
    )

    option.wait_for(
        state="visible",
        timeout=5000,
    )

    print(
        f"[BEFORE] "
        f"{mode_name} "
        f"checked="
        f"{option.get_attribute('aria-checked')}"
    )

    if (
            option.get_attribute("aria-checked")
            != "true"
    ):
        option.click()
        page.wait_for_timeout(500)

    # 菜单通常点击后关闭，所以重新打开调查状态
    open_mode_menu(page)

    selected = get_selected_mode(page)

    trigger = page.locator(
        MODEL_SWITCH_SELECTOR
    ).first

    trigger_text = trigger.inner_text().strip()

    print(
        f"[AFTER] selected={selected}"
    )
    print(
        f"[TRIGGER] {trigger_text}"
    )

    if selected != mode_name:
        raise RuntimeError(
            f"模式切换失败："
            f"期望={mode_name}，"
            f"实际={selected}"
        )

    # 关闭菜单，避免影响下一轮
    trigger.click()
    page.wait_for_timeout(200)


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

        print("=" * 90)
        print("YUANBAO MODE SWITCH SMOKE TEST")
        print("=" * 90)

        for index, mode in enumerate(
                MODES,
                start=1,
        ):
            print()
            print("-" * 90)
            print(
                f"[ROUND {index}] "
                f"{mode}"
            )

            select_mode(
                page=page,
                mode_name=mode,
            )

            print("[STATUS] PASS")

        print()
        print("=" * 90)
        print("MODE SWITCH STATUS: PASS")
        print("=" * 90)


if __name__ == "__main__":
    main()
