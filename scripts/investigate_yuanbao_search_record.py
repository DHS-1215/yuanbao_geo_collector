from __future__ import annotations

import re

from playwright.sync_api import Locator, sync_playwright

from app.browser.cdp import connect_cdp
from app.core.config import get_settings

SEARCH_TEXT_RE = re.compile(r"已搜索\d+次资料")


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


def print_ancestors(
        locator: Locator,
        max_depth: int = 8,
) -> None:
    result = locator.evaluate(
        """
        (el, maxDepth) => {
            const rows = [];

            let current = el;

            for (
                let depth = 0;
                current && depth < maxDepth;
                depth++
            ) {
                const attrs = {};

                for (const attr of current.attributes) {
                    attrs[attr.name] = attr.value;
                }

                const style =
                    window.getComputedStyle(current);

                rows.push({
                    depth,
                    tag: current.tagName,
                    id: current.id || '',
                    className:
                        typeof current.className === 'string'
                            ? current.className
                            : '',
                    role:
                        current.getAttribute('role'),
                    ariaLabel:
                        current.getAttribute('aria-label'),
                    tabindex:
                        current.getAttribute('tabindex'),
                    cursor: style.cursor,
                    text:
                        (
                            current.innerText
                            || current.textContent
                            || ''
                        ).trim(),
                    attrs,
                    html: current.outerHTML,
                });

                current = current.parentElement;
            }

            return rows;
        }
        """,
        max_depth,
    )

    for row in result:
        print("-" * 100)
        print(f"DEPTH:      {row['depth']}")
        print(f"TAG:        {row['tag']}")
        print(f"ID:         {row['id']}")
        print(f"ROLE:       {row['role']}")
        print(f"ARIA-LABEL: {row['ariaLabel']}")
        print(f"TABINDEX:   {row['tabindex']}")
        print(f"CURSOR:     {row['cursor']}")
        print(
            f"CLASS:      "
            f"{short(row['className'], 250)!r}"
        )
        print(
            f"TEXT:       "
            f"{short(row['text'], 350)!r}"
        )

        print("ATTRS:")

        for key, value in row["attrs"].items():
            if (
                    key.startswith("data-")
                    or key.startswith("aria-")
                    or key
                    in {
                "role",
                "tabindex",
                "href",
                "title",
            }
            ):
                print(
                    f"  {key}={value!r}"
                )

        print(
            f"HTML:       "
            f"{short(row['html'], 1000)}"
        )


def inspect_global_page(page) -> None:
    print()
    print("=" * 100)
    print("GLOBAL HREF")
    print("=" * 100)

    hrefs = page.locator("[href]")

    print(f"COUNT: {hrefs.count()}")

    for index in range(hrefs.count()):
        item = hrefs.nth(index)

        try:
            if not item.is_visible():
                continue

            print("-" * 100)
            print(
                f"[{index}] "
                f"{item.inner_text().strip()!r}"
            )
            print(
                f"HREF: "
                f"{item.get_attribute('href')}"
            )
        except Exception:
            pass

    for selector, title in [
        ('[role="dialog"]', "DIALOG"),
        ('[role="menu"]', "MENU"),
        ('[class*="source"]', "SOURCE CLASS"),
        ('[class*="Source"]', "Source CLASS"),
        ('[class*="search"]', "SEARCH CLASS"),
        ('[class*="Search"]', "Search CLASS"),
        ('[class*="result"]', "RESULT CLASS"),
        ('[class*="Result"]', "Result CLASS"),
    ]:
        print()
        print("=" * 100)
        print(title)
        print("=" * 100)

        items = page.locator(selector)

        print(f"COUNT: {items.count()}")

        for index in range(items.count()):
            item = items.nth(index)

            try:
                if not item.is_visible():
                    continue

                text = short(
                    item.inner_text(),
                    600,
                )

                class_name = short(
                    item.get_attribute("class"),
                    250,
                )

                print("-" * 100)
                print(f"INDEX: {index}")
                print(f"TEXT:  {text!r}")
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
            "YUANBAO SEARCH RECORD INVESTIGATION"
        )
        print("=" * 100)

        search_record = page.get_by_text(
            SEARCH_TEXT_RE,
            exact=True,
        )

        print(
            f"[SEARCH RECORD MATCHES] "
            f"{search_record.count()}"
        )

        if search_record.count() == 0:
            raise RuntimeError(
                "没有找到“已搜索X次资料”"
            )

        record = search_record.last

        print()
        print("[SEARCH RECORD]")
        print(
            record.inner_text().strip()
        )

        print()
        print("=" * 100)
        print("SEARCH RECORD ANCESTORS")
        print("=" * 100)

        print_ancestors(record)

        print()
        print("[BEFORE CLICK]")

        inspect_global_page(page)

        print()
        print("[ACTION] 尝试点击搜索记录")

        try:
            record.click(
                timeout=5000,
            )
        except Exception as exc:
            print(
                "[DIRECT CLICK FAILED] "
                f"{type(exc).__name__}: {exc}"
            )

            clickable = record.locator(
                "xpath=ancestor-or-self::*["
                "self::button "
                "or @role='button' "
                "or @tabindex"
                "][1]"
            )

            if clickable.count():
                print(
                    "[ACTION] 点击最近的可交互祖先"
                )

                clickable.first.click(
                    timeout=5000,
                )
            else:
                print(
                    "[CLICKABLE ANCESTOR] NOT FOUND"
                )

        page.wait_for_timeout(800)

        print()
        print("[AFTER CLICK]")

        inspect_global_page(page)

        print()
        print("=" * 100)
        print(
            "SEARCH RECORD INVESTIGATION COMPLETE"
        )
        print("=" * 100)


if __name__ == "__main__":
    main()
