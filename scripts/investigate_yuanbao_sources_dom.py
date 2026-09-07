from __future__ import annotations

from playwright.sync_api import Locator, sync_playwright

from app.browser.cdp import connect_cdp
from app.core.config import get_settings
from app.yuanbao.client import YuanbaoClient
from app.yuanbao.selectors import ANSWER_SELECTOR
from app.yuanbao.types import (
    YuanbaoMode,
    YuanbaoModel,
)


QUESTION = (
    "鸿茅药酒是正规药品吗？"
    "请基于公开网页资料回答，并附参考来源。"
)


def short(value: str | None, limit: int = 300) -> str:
    if not value:
        return ""

    value = value.strip()

    if len(value) > limit:
        return value[:limit] + "..."

    return value


def print_candidate(
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
                    attrs[attr.name] = attr.value;
                }

                return {
                    tag: el.tagName,
                    text:
                        (
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
        print(f"INDEX:      {index}")
        print(f"TAG:        {info['tag']}")
        print(f"ID:         {info['id']}")
        print(f"ROLE:       {info['role']}")
        print(f"ARIA-LABEL: {info['ariaLabel']}")
        print(f"TITLE:      {info['title']}")
        print(f"HREF:       {info['href']}")
        print(f"TEXT:       {short(info['text'], 400)!r}")
        print(
            f"CLASS:      "
            f"{short(info['className'], 250)!r}"
        )

        print("ATTRS:")

        for key, value in info["attrs"].items():
            if (
                key.startswith("data-")
                or key.startswith("aria-")
                or key
                in {
                    "href",
                    "title",
                    "role",
                }
            ):
                print(
                    f"  {key} = {value!r}"
                )

        print(
            f"HTML:       "
            f"{short(info['html'], 800)}"
        )

    except Exception as exc:
        print(
            f"[WARN] index={index}: {exc}"
        )


def inspect(
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
        print_candidate(
            locator.nth(index),
            index,
        )


def inspect_answer_tree(
    answer: Locator,
) -> None:
    result = answer.evaluate(
        """
        (answer) => {
            const root =
                answer.closest(
                    '.agent-chat__conv--ai__speech_show'
                )
                || answer.parentElement;

            const rows = [];
            let current = root;

            for (
                let depth = 0;
                current && depth < 6;
                depth++
            ) {
                rows.push({
                    depth,
                    tag: current.tagName,
                    id: current.id || '',
                    className:
                        typeof current.className === 'string'
                            ? current.className
                            : '',
                    text:
                        (
                            current.innerText
                            || current.textContent
                            || ''
                        ).trim(),
                    html: current.outerHTML,
                });

                current = current.parentElement;
            }

            return rows;
        }
        """
    )

    print()
    print("=" * 100)
    print("AI ANSWER ANCESTOR TREE")
    print("=" * 100)

    for row in result:
        print("-" * 100)
        print(f"DEPTH: {row['depth']}")
        print(f"TAG:   {row['tag']}")
        print(f"ID:    {row['id']}")
        print(
            f"CLASS: "
            f"{short(row['className'], 250)!r}"
        )
        print(
            f"TEXT:  "
            f"{short(row['text'], 500)!r}"
        )


def main() -> None:
    settings = get_settings()

    with sync_playwright() as playwright:
        browser = connect_cdp(
            playwright=playwright,
            cdp_url=settings.cdp_url,
        )

        page = browser.contexts[0].pages[0]

        client = YuanbaoClient(
            page=page,
            answer_timeout_seconds=180,
        )

        print("=" * 100)
        print(
            "YUANBAO SOURCE DOM INVESTIGATION"
        )
        print("=" * 100)

        client.new_chat()

        client.set_profile(
            model=YuanbaoModel.HY3,
            mode=YuanbaoMode.EXPERT,
        )

        print(
            "[PROFILE] Hy3 + 专家模式"
        )
        print(
            f"[QUESTION] {QUESTION}"
        )

        answer_text = client.ask(
            QUESTION
        )

        print()
        print("[ANSWER]")
        print(answer_text)

        answers = page.locator(
            ANSWER_SELECTOR
        )

        if answers.count() == 0:
            raise RuntimeError(
                "没有找到 AI 回答节点"
            )

        answer = answers.last

        ai_root = answer.locator(
            "xpath=ancestor::*"
            "[contains("
            "@class,"
            "'agent-chat__conv--ai__speech_show'"
            ")][1]"
        )

        if ai_root.count() == 0:
            raise RuntimeError(
                "没有找到 AI 回答根节点"
            )

        ai_root = ai_root.first

        inspect_answer_tree(
            answer
        )

        inspect(
            ai_root,
            "a",
            "A TAGS",
        )

        inspect(
            ai_root,
            "[href]",
            "ELEMENTS WITH HREF",
        )

        inspect(
            ai_root,
            "[data-url]",
            "DATA-URL",
        )

        inspect(
            ai_root,
            "[data-href]",
            "DATA-HREF",
        )

        inspect(
            ai_root,
            "[data-source]",
            "DATA-SOURCE",
        )

        inspect(
            ai_root,
            "[data-citation]",
            "DATA-CITATION",
        )

        inspect(
            ai_root,
            "[data-reference]",
            "DATA-REFERENCE",
        )

        inspect(
            ai_root,
            '[class*="source"]',
            'CLASS CONTAINS "source"',
        )

        inspect(
            ai_root,
            '[class*="Source"]',
            'CLASS CONTAINS "Source"',
        )

        inspect(
            ai_root,
            '[class*="citation"]',
            'CLASS CONTAINS "citation"',
        )

        inspect(
            ai_root,
            '[class*="Citation"]',
            'CLASS CONTAINS "Citation"',
        )

        inspect(
            ai_root,
            '[class*="reference"]',
            'CLASS CONTAINS "reference"',
        )

        inspect(
            ai_root,
            '[class*="Reference"]',
            'CLASS CONTAINS "Reference"',
        )

        inspect(
            ai_root,
            '[class*="search"]',
            'CLASS CONTAINS "search"',
        )

        inspect(
            ai_root,
            '[class*="Search"]',
            'CLASS CONTAINS "Search"',
        )

        inspect(
            ai_root,
            "button",
            "BUTTONS INSIDE AI ROOT",
        )

        inspect(
            ai_root,
            "[aria-label]",
            "ARIA ELEMENTS INSIDE AI ROOT",
        )

        print()
        print("=" * 100)
        print(
            "SOURCE DOM INVESTIGATION COMPLETE"
        )
        print("=" * 100)


if __name__ == "__main__":
    main()