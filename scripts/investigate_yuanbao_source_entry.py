from __future__ import annotations

from playwright.sync_api import Locator, sync_playwright

from app.browser.cdp import connect_cdp
from app.core.config import get_settings

AI_TURN_SELECTOR = ".agent-chat__list__item--ai"

SEARCH_GROUP_SELECTOR = (
    ".agent-process-timeline_group__G73lD"
)

SOURCE_TOOL_SELECTOR = (
    '[class*="ToolbarSearchGuid_searchGuidTool"]'
)


def short(
        value: str | None,
        limit: int = 500,
) -> str:
    if not value:
        return ""

    value = value.strip()

    if len(value) > limit:
        return value[:limit] + "..."

    return value


def inspect_tree(
        root: Locator,
        title: str,
) -> None:
    print()
    print("=" * 100)
    print(title)
    print("=" * 100)

    result = root.evaluate(
        """
        (root) => {
            return Array.from(
                root.querySelectorAll('*')
            ).map((el, index) => {
                const attrs = {};

                for (const attr of el.attributes) {
                    if (
                        attr.name.startsWith('data-')
                        || attr.name.startsWith('aria-')
                        || [
                            'href',
                            'role',
                            'tabindex',
                            'title'
                        ].includes(attr.name)
                    ) {
                        attrs[attr.name] = attr.value;
                    }
                }

                return {
                    index,
                    tag: el.tagName,
                    text: (
                        el.innerText
                        || el.textContent
                        || ''
                    ).trim(),
                    className:
                        typeof el.className === 'string'
                            ? el.className
                            : '',
                    href: el.getAttribute('href'),
                    role: el.getAttribute('role'),
                    attrs,
                    html: el.outerHTML,
                };
            });
        }
        """
    )

    print(f"COUNT: {len(result)}")

    for item in result:
        text = item["text"] or ""
        class_name = item["className"] or ""
        href = item["href"]

        interesting = (
                bool(text)
                or bool(href)
                or bool(item["attrs"])
                or "search" in class_name.lower()
                or "source" in class_name.lower()
                or "result" in class_name.lower()
                or "reference" in class_name.lower()
        )

        if not interesting:
            continue

        print("-" * 100)
        print(f"INDEX: {item['index']}")
        print(f"TAG:   {item['tag']}")
        print(f"ROLE:  {item['role']}")
        print(f"HREF:  {href}")
        print(
            f"TEXT:  "
            f"{short(text, 350)!r}"
        )
        print(
            f"CLASS: "
            f"{short(class_name, 250)!r}"
        )

        if item["attrs"]:
            print("ATTRS:")

            for key, value in (
                    item["attrs"].items()
            ):
                print(
                    f"  {key}={value!r}"
                )

        print(
            "HTML:  "
            f"{short(item['html'], 800)}"
        )


def inspect_visible_overlays(page) -> None:
    print()
    print("=" * 100)
    print("VISIBLE OVERLAYS / PANELS")
    print("=" * 100)

    selectors = [
        '[role="dialog"]',
        '[role="menu"]',
        '[class*="source"]',
        '[class*="Source"]',
        '[class*="reference"]',
        '[class*="Reference"]',
        '[class*="result"]',
        '[class*="Result"]',
        '[class*="drawer"]',
        '[class*="Drawer"]',
        '[class*="popup"]',
        '[class*="Popup"]',
    ]

    seen = set()

    for selector in selectors:
        items = page.locator(selector)

        for index in range(items.count()):
            item = items.nth(index)

            try:
                if not item.is_visible():
                    continue

                text = short(
                    item.inner_text(),
                    700,
                )

                class_name = short(
                    item.get_attribute("class"),
                    250,
                )

                key = (
                    text,
                    class_name,
                )

                if key in seen:
                    continue

                seen.add(key)

                print("-" * 100)
                print(
                    f"SELECTOR: {selector}"
                )
                print(
                    f"TEXT:  {text!r}"
                )
                print(
                    f"CLASS: {class_name!r}"
                )

            except Exception:
                pass


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
            "YUANBAO SOURCE ENTRY INVESTIGATION"
        )
        print("=" * 100)

        ai_turns = page.locator(
            AI_TURN_SELECTOR
        )

        if ai_turns.count() == 0:
            raise RuntimeError(
                "没有找到 AI 回答"
            )

        ai_turn = ai_turns.last

        # --------------------------------------------------
        # A. 已搜索资料
        # --------------------------------------------------

        groups = ai_turn.locator(
            SEARCH_GROUP_SELECTOR
        )

        print(
            f"[SEARCH GROUP COUNT] "
            f"{groups.count()}"
        )

        if groups.count():
            group = groups.last

            header = group.locator(
                '[role="button"]'
            ).first

            expanded = (
                header.get_attribute(
                    "aria-expanded"
                )
            )

            print(
                f"[SEARCH GROUP EXPANDED] "
                f"{expanded}"
            )

            if expanded != "true":
                print(
                    "[ACTION] 展开搜索记录"
                )

                header.click()
                page.wait_for_timeout(500)

            print(
                "[SEARCH GROUP TEXT]"
            )
            print(
                short(
                    group.inner_text(),
                    2000,
                )
            )

            inspect_tree(
                group,
                "SEARCH GROUP TREE",
            )

        # --------------------------------------------------
        # B. “源”按钮
        # --------------------------------------------------

        source_tools = page.locator(
            SOURCE_TOOL_SELECTOR
        )

        print()
        print(
            f"[SOURCE TOOL COUNT] "
            f"{source_tools.count()}"
        )

        visible_source = None

        for index in range(
                source_tools.count()
        ):
            item = source_tools.nth(index)

            if item.is_visible():
                visible_source = item

                print(
                    f"[SOURCE TOOL INDEX] "
                    f"{index}"
                )
                print(
                    f"[SOURCE TOOL TEXT] "
                    f"{item.inner_text()!r}"
                )

                inspect_tree(
                    item,
                    "SOURCE TOOL TREE",
                )

                break

        if visible_source is None:
            print(
                "[SOURCE TOOL] "
                "没有找到可见的“源”"
            )

        else:
            print()
            print(
                "[ACTION] 点击“源”"
            )

            visible_source.click(
                timeout=5000,
            )

            page.wait_for_timeout(700)

            inspect_visible_overlays(
                page
            )

            print()
            print("=" * 100)
            print("VISIBLE LINKS AFTER SOURCE CLICK")
            print("=" * 100)

            links = page.locator(
                "a[href]"
            )

            print(
                f"COUNT: {links.count()}"
            )

            visible_count = 0

            for index in range(
                    links.count()
            ):
                link = links.nth(index)

                try:
                    if not link.is_visible():
                        continue

                    visible_count += 1

                    text = short(
                        link.inner_text(),
                        250,
                    )

                    href = (
                        link.get_attribute(
                            "href"
                        )
                    )

                    print("-" * 100)
                    print(
                        f"INDEX: {index}"
                    )
                    print(
                        f"TEXT: {text!r}"
                    )
                    print(
                        f"HREF: {href}"
                    )

                except Exception:
                    pass

            print(
                f"[VISIBLE LINK COUNT] "
                f"{visible_count}"
            )

        print()
        print("=" * 100)
        print(
            "SOURCE ENTRY INVESTIGATION COMPLETE"
        )
        print("=" * 100)


if __name__ == "__main__":
    main()
