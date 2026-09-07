from playwright.sync_api import sync_playwright

from app.browser.cdp import connect_cdp
from app.core.config import get_settings
from app.yuanbao.client import YuanbaoClient
from app.yuanbao.selectors import (
    ANSWER_SELECTOR,
    QUESTION_SELECTOR,
)

QUESTIONS = [
    "请只回答：第一题采集成功",
    "请只回答：第二题采集成功",
]


def main() -> None:
    settings = get_settings()

    with sync_playwright() as playwright:
        browser = connect_cdp(
            playwright=playwright,
            cdp_url=settings.cdp_url,
        )

        context = browser.contexts[0]
        page = context.pages[0]

        client = YuanbaoClient(
            page=page,
            answer_timeout_seconds=60,
        )

        print("=" * 80)
        print("YUANBAO MULTI CHAT SMOKE TEST")
        print("=" * 80)

        for index, question in enumerate(
                QUESTIONS,
                start=1,
        ):
            print()
            print("-" * 80)
            print(f"[ROUND {index}]")

            client.new_chat()

            print("[NEW CHAT] PASS")
            print(f"[QUESTION] {question}")

            answer = client.ask(question)

            question_count = page.locator(
                QUESTION_SELECTOR
            ).count()

            answer_count = page.locator(
                ANSWER_SELECTOR
            ).count()

            print(f"[ANSWER] {answer}")
            print(
                f"[QUESTION COUNT] "
                f"{question_count}"
            )
            print(
                f"[ANSWER COUNT]   "
                f"{answer_count}"
            )
            print(f"[URL] {page.url}")

            if question_count != 1:
                raise RuntimeError(
                    f"第 {index} 轮问题数量异常："
                    f"{question_count}"
                )

            if answer_count != 1:
                raise RuntimeError(
                    f"第 {index} 轮回答数量异常："
                    f"{answer_count}"
                )

        print()
        print("=" * 80)
        print("MULTI CHAT STATUS: PASS")
        print("=" * 80)


if __name__ == "__main__":
    main()
