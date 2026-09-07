from __future__ import annotations

from playwright.sync_api import Locator, sync_playwright

from app.browser.cdp import connect_cdp
from app.core.config import get_settings

AI_ROOT_SELECTOR = (
    ".agent-chat__list__item--ai"
)

DEEP_SEARCH_SELECTOR = (
    ".hyc-component-deep-search-agent"
)

PROCESSED_TOGGLE_SELECTOR = (
    ".hyc-component-deep-search-agent"
    "__think__header__toggle"
)


def short(
        value: str | None,
        limit: int = 400,
) -> str:
    if not value:
        return ""

    value = value.strip()

    if len(value) > limit:
        return value[:limit] + "..."

    return value


def inspect_elements(
        root: Locator,
        selector: str,
        title: str,
) -> None:
    print()
    print("=" * 100)
    print(title)
    print("=" * 100)

    locator = root.locator(selector)

    print(f"COUNT: {locator.count()}")

    for index in range(locator.count()):
        element = locator.nth(index)

        try:
            if not element.is_visible():
                continue

            info = element.evaluate(
                """
                (el) => {
                    const attrs = {};

                    for (const attr of el.attributes) {
                        attrs[attr.name] = attr.value;
                    }

                    return {
                        tag: el.tagName,
                        text: (
                            el.innerText
                            || el.textContent
                            || ''
                        ).trim(),
                        id: el.id || '',
                        className:
                            typeof el.className === 'string'
                                ? el.className
                                : '',
                        href: el.getAttribute('href'),
                        role: el.getAttribute('role'),
                        ariaLabel:
                            el.getAttribute('aria-label'),
                        title:
                            el.getAttribute('title'),
                        attrs,
                        html: el.outerHTML,
                    };
                }
                """
            )

            print("-" * 100)
            print(f"INDEX: {index}")
            print(f"TAG:   {info['tag']}")
            print(f"ID:    {info['id']}")
            print(f"ROLE:  {info['role']}")
            print(
                f"ARIA:  {info['ariaLabel']}"
            )
            print(
                f"TITLE: {info['title']}"
            )
            print(
                f"HREF:  {info['href']}"
            )
            print(
                f"TEXT:  "
                f"{short(info['text'])!r}"
            )
            print(
                f"CLASS: "
                f"{short(info['className'], 250)!r}"
            )

            print("ATTRS:")

            for key, value in (
                    info["attrs"].items()
            ):
                if (
                        key.startswith("data-")
                        or key.startswith("aria-")
                        or key
                        in {
                    "href",
                    "role",
                    "title",
                }
                ):
                    print(
                        f"  {key}={value!r}"
                    )

            print(
                f"HTML: "
                f"{short(info['html'], 1000)}"
            )

        except Exception as exc:
            print(
                f"[WARN] "
                f"index={index}: {exc}"
            )


def main() -> None:
    settings = get_settings()

    with sync_playwright() as playwright:
        browser = connect_cdp(
            playwright=playwright,
            cdp_url=settings.cdp_url,
        )

        page = browser.contexts[0].pages[0]

        print("=" * 100)
        print(
            "YUANBAO PROCESSED PANEL "
            "INVESTIGATION"
        )
        print("=" * 100)

        ai_turns = page.locator(
            AI_ROOT_SELECTOR
        )

        if ai_turns.count() == 0:
            raise RuntimeError(
                "没有找到 AI 回答"
            )

        ai_turn = ai_turns.last

        deep_search = ai_turn.locator(
            DEEP_SEARCH_SELECTOR
        ).first

        if deep_search.count() == 0:
            raise RuntimeError(
                "当前回答没有 Deep Search Agent"
            )

        print(
            "[DEEP SEARCH] FOUND"
        )

        print()
        print("[TEXT BEFORE]")
        print(
            short(
                deep_search.inner_text(),
                1000,
            )
        )

        inspect_elements(
            deep_search,
            "button",
            "BUTTONS BEFORE EXPAND",
        )

        inspect_elements(
            deep_search,
            "a",
            "A TAGS BEFORE EXPAND",
        )

        toggle = deep_search.locator(
            PROCESSED_TOGGLE_SELECTOR
        ).first

        if toggle.count() == 0:
            raise RuntimeError(
                "没有找到“已处理”展开按钮"
            )

        print()
        print("[ACTION] 展开“已处理”")

        toggle.click()

        page.wait_for_timeout(700)

        print()
        print("[TEXT AFTER]")
        print(
            short(
                deep_search.inner_text(),
                3000,
            )
        )

        inspect_elements(
            deep_search,
            "button",
            "BUTTONS AFTER EXPAND",
        )

        inspect_elements(
            deep_search,
            "a",
            "A TAGS AFTER EXPAND",
        )

        inspect_elements(
            deep_search,
            "[href]",
            "HREF AFTER EXPAND",
        )

        inspect_elements(
            deep_search,
            '[class*="search"]',
            'CLASS CONTAINS "search"',
        )

        inspect_elements(
            deep_search,
            '[class*="Search"]',
            'CLASS CONTAINS "Search"',
        )

        inspect_elements(
            deep_search,
            '[class*="tool"]',
            'CLASS CONTAINS "tool"',
        )

        inspect_elements(
            deep_search,
            '[class*="Tool"]',
            'CLASS CONTAINS "Tool"',
        )

        inspect_elements(
            deep_search,
            '[class*="web"]',
            'CLASS CONTAINS "web"',
        )

        inspect_elements(
            deep_search,
            '[class*="Web"]',
            'CLASS CONTAINS "Web"',
        )

        inspect_elements(
            deep_search,
            '[class*="reference"]',
            'CLASS CONTAINS "reference"',
        )

        inspect_elements(
            deep_search,
            '[class*="source"]',
            'CLASS CONTAINS "source"',
        )

        print()
        print("=" * 100)
        print(
            "PROCESSED PANEL "
            "INVESTIGATION COMPLETE"
        )
        print("=" * 100)


if __name__ == "__main__":
    main()
