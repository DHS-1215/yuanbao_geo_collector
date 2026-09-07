from __future__ import annotations

from playwright.sync_api import Locator, Page, sync_playwright

from app.browser.cdp import connect_cdp
from app.core.config import get_settings

QUESTION_TEXT = "请用一句话介绍腾讯元宝。"
ANSWER_TEXT = "我是元宝，是由腾讯开发的大模型。"


def print_ancestors(
        locator: Locator,
        title: str,
        max_depth: int = 8,
) -> None:
    print()
    print("=" * 100)
    print(title)
    print("=" * 100)

    if locator.count() == 0:
        print("[NOT FOUND]")
        return

    element = locator.first

    result = element.evaluate(
        """
        (el, maxDepth) => {
            const rows = [];

            let current = el;

            for (let depth = 0; current && depth < maxDepth; depth++) {
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
                    dataTestId: current.getAttribute('data-testid'),
                    dataRole: current.getAttribute('data-role'),
                    dataIndex: current.getAttribute('data-index'),
                    text:
                        (current.innerText || current.textContent || '').trim(),
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

        if len(text) > 300:
            text = text[:300] + "..."

        if len(class_name) > 250:
            class_name = class_name[:250] + "..."

        print("-" * 100)
        print(f"DEPTH:       {row['depth']}")
        print(f"TAG:         {row['tag']}")
        print(f"ID:          {row['id']}")
        print(f"ROLE:        {row['role']}")
        print(f"ARIA-LABEL:  {row['ariaLabel']}")
        print(f"DATA-TESTID: {row['dataTestId']}")
        print(f"DATA-ROLE:   {row['dataRole']}")
        print(f"DATA-INDEX:  {row['dataIndex']}")
        print(f"CLASS:       {class_name!r}")
        print(f"TEXT:        {text!r}")


def inspect_buttons(page: Page) -> None:
    print()
    print("=" * 100)
    print("VISIBLE BUTTON / ARIA CONTROLS")
    print("=" * 100)

    locator = page.locator("button, [aria-label]")

    print(f"COUNT: {locator.count()}")

    for index in range(locator.count()):
        element = locator.nth(index)

        try:
            if not element.is_visible():
                continue

            info = element.evaluate(
                """
                (el) => ({
                    tag: el.tagName,
                    text: (el.innerText || el.textContent || '').trim(),
                    id: el.id || '',
                    ariaLabel: el.getAttribute('aria-label'),
                    title: el.getAttribute('title'),
                    dataDesc: el.getAttribute('data-desc'),
                    dataTestId: el.getAttribute('data-testid'),
                    className:
                        typeof el.className === 'string'
                            ? el.className
                            : '',
                })
                """
            )

            text = info["text"] or ""
            class_name = info["className"] or ""

            if len(text) > 100:
                text = text[:100] + "..."

            if len(class_name) > 180:
                class_name = class_name[:180] + "..."

            print("-" * 100)
            print(f"INDEX:       {index}")
            print(f"TAG:         {info['tag']}")
            print(f"ID:          {info['id']}")
            print(f"TEXT:        {text!r}")
            print(f"ARIA-LABEL:  {info['ariaLabel']}")
            print(f"TITLE:       {info['title']}")
            print(f"DATA-DESC:   {info['dataDesc']}")
            print(f"DATA-TESTID: {info['dataTestId']}")
            print(f"CLASS:       {class_name!r}")

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

        print("=" * 100)
        print("YUANBAO RESPONSE DOM INVESTIGATION")
        print("=" * 100)
        print(f"[TITLE] {page.title()}")
        print(f"[URL]   {page.url}")

        question = page.get_by_text(
            QUESTION_TEXT,
            exact=True,
        )

        answer = page.get_by_text(
            ANSWER_TEXT,
            exact=True,
        )

        print(f"[QUESTION MATCHES] {question.count()}")
        print(f"[ANSWER MATCHES]   {answer.count()}")

        print_ancestors(
            question,
            "QUESTION ANCESTORS",
        )

        print_ancestors(
            answer,
            "ANSWER ANCESTORS",
        )

        inspect_buttons(page)

        print()
        print("=" * 100)
        print("INVESTIGATION COMPLETE")
        print("=" * 100)


if __name__ == "__main__":
    main()
