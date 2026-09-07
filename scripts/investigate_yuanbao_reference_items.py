from __future__ import annotations

from playwright.sync_api import Locator, sync_playwright

from app.browser.cdp import connect_cdp
from app.core.config import get_settings

REFERENCE_LIST_SELECTOR = (
    ".agent-dialogue-references__list"
)

REFERENCE_ITEM_SELECTOR = (
    ".agent-dialogue-references__item"
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


def inspect_item(
        item: Locator,
        index: int,
) -> None:
    info = item.evaluate(
        """
        (el) => {
            const attrs = {};

            for (const attr of el.attributes) {
                attrs[attr.name] = attr.value;
            }

            const descendants = Array.from(
                el.querySelectorAll('*')
            ).map((node) => {
                const nodeAttrs = {};

                for (const attr of node.attributes) {
                    nodeAttrs[attr.name] = attr.value;
                }

                return {
                    tag: node.tagName,
                    text: (
                        node.innerText
                        || node.textContent
                        || ''
                    ).trim(),
                    className:
                        typeof node.className === 'string'
                            ? node.className
                            : '',
                    href:
                        node.getAttribute('href'),
                    src:
                        node.getAttribute('src'),
                    role:
                        node.getAttribute('role'),
                    attrs: nodeAttrs,
                };
            });

            const reactInfo = [];

            function collectStrings(
                obj,
                path,
                depth,
                seen
            ) {
                if (
                    obj === null
                    || obj === undefined
                    || depth > 4
                ) {
                    return;
                }

                if (
                    typeof obj === 'string'
                    || typeof obj === 'number'
                    || typeof obj === 'boolean'
                ) {
                    const value = String(obj);

                    if (
                        /url|href|link|title|domain|source/i.test(path)
                        || /^https?:\\/\\//i.test(value)
                    ) {
                        reactInfo.push({
                            path,
                            value,
                        });
                    }

                    return;
                }

                if (
                    typeof obj !== 'object'
                    || seen.has(obj)
                ) {
                    return;
                }

                seen.add(obj);

                let entries;

                try {
                    entries = Object.entries(obj);
                } catch {
                    return;
                }

                for (const [key, value] of entries) {
                    if (
                        key === 'children'
                        && depth >= 2
                    ) {
                        continue;
                    }

                    collectStrings(
                        value,
                        path
                            ? `${path}.${key}`
                            : key,
                        depth + 1,
                        seen
                    );
                }
            }

            const reactKeys = Object.keys(el).filter(
                (key) =>
                    key.startsWith('__reactProps$')
                    || key.startsWith('__reactFiber$')
            );

            for (const key of reactKeys) {
                try {
                    const value = el[key];

                    if (
                        key.startsWith('__reactProps$')
                    ) {
                        collectStrings(
                            value,
                            key,
                            0,
                            new WeakSet()
                        );
                    }

                    if (
                        key.startsWith('__reactFiber$')
                        && value
                    ) {
                        collectStrings(
                            value.memoizedProps,
                            `${key}.memoizedProps`,
                            0,
                            new WeakSet()
                        );

                        collectStrings(
                            value.pendingProps,
                            `${key}.pendingProps`,
                            0,
                            new WeakSet()
                        );
                    }
                } catch {
                    // ignore
                }
            }

            return {
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
                attrs,
                descendants,
                reactInfo,
                html: el.outerHTML,
            };
        }
        """
    )

    print()
    print("=" * 100)
    print(f"REFERENCE ITEM {index}")
    print("=" * 100)

    print(
        f"TEXT:\n{short(info['text'], 1500)}"
    )

    print()
    print(
        f"CLASS: {info['className']!r}"
    )

    print()
    print("ITEM ATTRS:")

    if info["attrs"]:
        for key, value in info["attrs"].items():
            print(
                f"  {key} = {value!r}"
            )
    else:
        print("  <none>")

    print()
    print("DESCENDANTS:")

    for child in info["descendants"]:
        interesting = (
                child["href"]
                or child["src"]
                or child["attrs"]
                or "url" in child["className"].lower()
                or "link" in child["className"].lower()
                or "source" in child["className"].lower()
                or "reference" in child["className"].lower()
        )

        if not interesting:
            continue

        print("-" * 100)
        print(
            f"TAG:   {child['tag']}"
        )
        print(
            f"TEXT:  "
            f"{short(child['text'], 300)!r}"
        )
        print(
            f"CLASS: "
            f"{short(child['className'], 250)!r}"
        )
        print(
            f"HREF:  {child['href']}"
        )
        print(
            f"SRC:   {child['src']}"
        )

        if child["attrs"]:
            print("ATTRS:")

            for key, value in (
                    child["attrs"].items()
            ):
                print(
                    f"  {key}={value!r}"
                )

    print()
    print("REACT DATA:")

    if info["reactInfo"]:
        for entry in info["reactInfo"]:
            print(
                f"  {entry['path']} "
                f"= {entry['value']!r}"
            )
    else:
        print("  <none>")

    print()
    print(
        "HTML: "
        f"{short(info['html'], 2000)}"
    )


def main() -> None:
    settings = get_settings()

    with sync_playwright() as playwright:
        browser = connect_cdp(
            playwright=playwright,
            cdp_url=settings.cdp_url,
        )

        context = browser.contexts[0]
        page = context.pages[0]

        print("=" * 100)
        print(
            "YUANBAO REFERENCE ITEM INVESTIGATION"
        )
        print("=" * 100)

        reference_list = page.locator(
            REFERENCE_LIST_SELECTOR
        )

        if reference_list.count() == 0:
            raise RuntimeError(
                "没有找到引用来源列表，"
                "请先点击回答下方的“源”"
            )

        items = page.locator(
            REFERENCE_ITEM_SELECTOR
        )

        print(
            f"[REFERENCE COUNT] "
            f"{items.count()}"
        )

        if items.count() == 0:
            raise RuntimeError(
                "没有找到引用来源条目"
            )

        # 第一轮先调查前三条即可
        limit = min(
            items.count(),
            3,
        )

        for index in range(limit):
            inspect_item(
                items.nth(index),
                index + 1,
            )

        print()
        print("=" * 100)
        print(
            "REFERENCE ITEM INVESTIGATION COMPLETE"
        )
        print("=" * 100)


if __name__ == "__main__":
    main()
