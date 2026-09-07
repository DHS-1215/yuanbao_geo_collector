from __future__ import annotations

from playwright.sync_api import Page, sync_playwright

from app.browser.cdp import connect_cdp
from app.core.config import get_settings
from app.yuanbao.selectors import MODEL_SWITCH_SELECTOR


MODE_NAMES = {
    "快速回答",
    "深度思考",
    "专家模式",
}

MODEL_NAMES = {
    "Hy3",
    "DeepSeek",
    "Hy4 preview",
}


def first_line(text: str) -> str:
    return text.strip().splitlines()[0].strip()


def open_main_menu(page: Page) -> None:
    trigger = page.locator(
        MODEL_SWITCH_SELECTOR
    ).first

    trigger.wait_for(
        state="visible",
        timeout=5000,
    )

    if trigger.get_attribute("aria-expanded") != "true":
        trigger.click()
        page.wait_for_timeout(300)


def open_model_menu(page: Page) -> None:
    open_main_menu(page)

    entry = page.locator(
        'button[role="menuitem"][aria-label="选择模型"]'
    ).first

    entry.wait_for(
        state="visible",
        timeout=5000,
    )

    if entry.get_attribute("aria-expanded") != "true":
        entry.click()
        page.wait_for_timeout(300)


def get_state(page: Page) -> dict:
    open_model_menu(page)

    radios = page.locator(
        'button[role="menuitemradio"]'
    )

    selected_mode = None
    selected_model = None

    modes = {}
    models = {}

    for index in range(radios.count()):
        item = radios.nth(index)

        if not item.is_visible():
            continue

        name = first_line(
            item.inner_text()
        )

        checked = (
            item.get_attribute("aria-checked")
            == "true"
        )

        disabled = (
            item.get_attribute("aria-disabled")
            == "true"
        )

        info = {
            "checked": checked,
            "disabled": disabled,
        }

        if name in MODE_NAMES:
            modes[name] = info

            if checked:
                selected_mode = name

        elif name in MODEL_NAMES:
            models[name] = info

            if checked:
                selected_model = name

    return {
        "mode": selected_mode,
        "model": selected_model,
        "modes": modes,
        "models": models,
    }


def print_state(
    title: str,
    state: dict,
) -> None:
    print()
    print("=" * 90)
    print(title)
    print("=" * 90)

    print(f"[SELECTED MODE]  {state['mode']}")
    print(f"[SELECTED MODEL] {state['model']}")

    print()
    print("[MODES]")

    for name, info in state["modes"].items():
        print(
            f"  {name:<8} "
            f"checked={info['checked']} "
            f"disabled={info['disabled']}"
        )

    print()
    print("[MODELS]")

    for name, info in state["models"].items():
        print(
            f"  {name:<12} "
            f"checked={info['checked']} "
            f"disabled={info['disabled']}"
        )


def close_menu(page: Page) -> None:
    trigger = page.locator(
        MODEL_SWITCH_SELECTOR
    ).first

    if trigger.get_attribute("aria-expanded") == "true":
        trigger.click()
        page.wait_for_timeout(200)


def select_model(
    page: Page,
    model_name: str,
) -> None:
    open_model_menu(page)

    radios = page.locator(
        'button[role="menuitemradio"]'
    )

    target = None

    for index in range(radios.count()):
        item = radios.nth(index)

        if not item.is_visible():
            continue

        name = first_line(
            item.inner_text()
        )

        if name == model_name:
            target = item
            break

    if target is None:
        raise RuntimeError(
            f"没有找到模型：{model_name}"
        )

    print()
    print(
        f"[SELECT MODEL] {model_name}"
    )

    print(
        "[BEFORE] "
        f"checked="
        f"{target.get_attribute('aria-checked')} "
        f"disabled="
        f"{target.get_attribute('aria-disabled')}"
    )

    target.click()

    page.wait_for_timeout(700)


def main() -> None:
    settings = get_settings()

    with sync_playwright() as playwright:
        browser = connect_cdp(
            playwright=playwright,
            cdp_url=settings.cdp_url,
        )

        context = browser.contexts[0]
        page = context.pages[0]

        print("=" * 90)
        print(
            "YUANBAO MODEL / MODE COMPATIBILITY"
        )
        print("=" * 90)

        state = get_state(page)

        print_state(
            "INITIAL STATE",
            state,
        )

        close_menu(page)

        for model in [
            "Hy3",
            "DeepSeek",
            "Hy4 preview",
            "Hy3",
        ]:
            select_model(
                page=page,
                model_name=model,
            )

            state = get_state(page)

            print_state(
                f"AFTER SELECT {model}",
                state,
            )

            close_menu(page)

        print()
        print("=" * 90)
        print(
            "COMPATIBILITY INVESTIGATION COMPLETE"
        )
        print("=" * 90)


if __name__ == "__main__":
    main()