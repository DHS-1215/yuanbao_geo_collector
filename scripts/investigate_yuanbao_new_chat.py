from __future__ import annotations

from playwright.sync_api import Locator, Page, sync_playwright

from app.browser.cdp import connect_cdp
from app.core.config import get_settings
from app.yuanbao.selectors import (
    ANSWER_SELECTOR,
    INPUT_SELECTOR,
    QUESTION_SELECTOR,
)

NEW_CHAT_TEXT = "新对话"


def print_ancestors(
        locator: Locator,
        max_depth: int = 6,
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
                rows.push({
                    depth,
                    tag: current.tagName,
                    id: current.id || '',
                    className:
                        typeof current.className === 'string'
                            ? current.className
                            : '',
                    role: current.getAttribute('role'),
                    ariaLabel: current.getAttribute('aria-label'),
                    dataDesc: current.getAttribute('data-desc'),
                    href: current.getAttribute('href'),
                    text:
                        (
                            current.innerText
                            || current.textContent
                            || ''
                        ).trim(),
                });

                current = current.parentElement;
            }

            return rows;
        }
        """,
        max_depth,
    )

    for row in result:
        text = row["text"] or ""
        class_name = row["className"] or ""

        if len(text) > 200:
            text = text[:200] + "..."

        if len(class_name) > 220:
            class_name = class_name[:220] + "..."

        print("-" * 90)
        print(f"DEPTH:      {row['depth']}")
        print(f"TAG:        {row['tag']}")
        print(f"ID:         {row['id']}")
        print(f"ROLE:       {row['role']}")
        print(f"ARIA-LABEL: {row['ariaLabel']}")
        print(f"DATA-DESC:  {row['dataDesc']}")
        print(f"HREF:       {row['href']}")
        print(f"CLASS:      {class_name!r}")
        print(f"TEXT:       {text!r}")


def find_visible_new_chat(
        page: Page,
) -> Locator:
    locator = page.get_by_text(
        NEW_CHAT_TEXT,
        exact=True,
    )

    print(
        f"[NEW CHAT MATCHES] "
        f"{locator.count()}"
    )

    for index in range(locator.count()):
        candidate = locator.nth(index)

        if candidate.is_visible():
            print(
                f"[NEW CHAT] "
                f"使用可见匹配 index={index}"
            )
            return candidate

    raise RuntimeError(
        "没有找到可见的“新对话”控件"
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

        print("=" * 90)
        print(
            "YUANBAO NEW CHAT INVESTIGATION"
        )
        print("=" * 90)

        before_url = page.url

        before_questions = page.locator(
            QUESTION_SELECTOR
        ).count()

        before_answers = page.locator(
            ANSWER_SELECTOR
        ).count()

        print(f"[BEFORE URL]       {before_url}")
        print(
            f"[BEFORE QUESTIONS] "
            f"{before_questions}"
        )
        print(
            f"[BEFORE ANSWERS]   "
            f"{before_answers}"
        )

        new_chat = find_visible_new_chat(page)

        print()
        print("=" * 90)
        print("NEW CHAT DOM")
        print("=" * 90)

        print_ancestors(new_chat)

        print()
        print("[ACTION] 点击新对话")

        new_chat.click()

        page.wait_for_timeout(1500)

        after_url = page.url

        after_questions = page.locator(
            QUESTION_SELECTOR
        ).count()

        after_answers = page.locator(
            ANSWER_SELECTOR
        ).count()

        editor_count = page.locator(
            INPUT_SELECTOR
        ).count()

        editor_visible = False

        if editor_count:
            editor_visible = (
                page.locator(INPUT_SELECTOR)
                .first
                .is_visible()
            )

        print()
        print("=" * 90)
        print("AFTER NEW CHAT")
        print("=" * 90)

        print(f"[AFTER URL]        {after_url}")
        print(
            f"[AFTER QUESTIONS]  "
            f"{after_questions}"
        )
        print(
            f"[AFTER ANSWERS]    "
            f"{after_answers}"
        )
        print(
            f"[EDITOR COUNT]     "
            f"{editor_count}"
        )
        print(
            f"[EDITOR VISIBLE]   "
            f"{editor_visible}"
        )

        if (
                after_questions == 0
                and after_answers == 0
                and editor_visible
        ):
            print()
            print(
                "[RESULT] 新对话已进入干净上下文"
            )
            print("NEW CHAT STATUS: PASS")
        else:
            print()
            print(
                "[RESULT] 页面未完全清空，"
                "需要继续调查"
            )
            print(
                "NEW CHAT STATUS: CHECK"
            )

        print()
        print("=" * 90)
        print("INVESTIGATION COMPLETE")
        print("=" * 90)


if __name__ == "__main__":
    main()
