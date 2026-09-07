from __future__ import annotations

import time

from playwright.sync_api import Page, sync_playwright

from app.browser.cdp import connect_cdp
from app.core.config import get_settings


INPUT_SELECTOR = '.ql-editor[contenteditable="true"]'
SEND_SELECTOR = '#yuanbao-send-btn'

ANSWER_SELECTOR = (
    '.agent-chat__conv--ai__speech_show .hyc-content-md'
)

ANSWER_DONE_SELECTOR = (
    '.agent-chat__conv--ai__speech_show .hyc-content-md-done'
)

TEST_QUESTION = (
    "请分5点介绍人工智能的发展历程，"
    "每一点不少于100字。"
)


def print_state(
    page: Page,
    elapsed: float,
) -> None:
    answers = page.locator(ANSWER_SELECTOR)
    done_answers = page.locator(ANSWER_DONE_SELECTOR)

    answer_count = answers.count()
    done_count = done_answers.count()

    latest_text = ""

    if answer_count > 0:
        try:
            latest_text = answers.last.inner_text().strip()
        except Exception:
            latest_text = ""

    if len(latest_text) > 120:
        latest_text = latest_text[:120] + "..."

    send = page.locator(SEND_SELECTOR)

    send_aria = None
    send_class = None

    if send.count():
        try:
            send_aria = send.first.get_attribute("aria-label")
            send_class = send.first.get_attribute("class")
        except Exception:
            pass

    regenerate_count = page.locator(
        '[aria-label="重新生成"]'
    ).count()

    print("-" * 90)
    print(f"[TIME]       {elapsed:.1f}s")
    print(f"[ANSWERS]    {answer_count}")
    print(f"[DONE]       {done_count}")
    print(f"[REGENERATE] {regenerate_count}")
    print(f"[SEND ARIA]  {send_aria}")
    print(f"[SEND CLASS] {send_class}")
    print(f"[TEXT]       {latest_text!r}")


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
        print("YUANBAO STREAMING STATE INVESTIGATION")
        print("=" * 90)

        editor = page.locator(INPUT_SELECTOR).first

        editor.click()
        editor.fill(TEST_QUESTION)

        send = page.locator(SEND_SELECTOR).first

        send.wait_for(
            state="visible",
            timeout=5000,
        )

        before_answer_count = page.locator(
            ANSWER_SELECTOR
        ).count()

        before_done_count = page.locator(
            ANSWER_DONE_SELECTOR
        ).count()

        print(f"[BEFORE ANSWERS] {before_answer_count}")
        print(f"[BEFORE DONE]    {before_done_count}")

        send.click()

        print(f"[QUESTION] {TEST_QUESTION}")
        print("[SEND] 已发送")

        start = time.monotonic()

        for _ in range(60):
            elapsed = time.monotonic() - start

            print_state(
                page=page,
                elapsed=elapsed,
            )

            answers = page.locator(ANSWER_SELECTOR)
            done_answers = page.locator(
                ANSWER_DONE_SELECTOR
            )

            current_answer_count = answers.count()
            current_done_count = done_answers.count()

            new_answer_created = (
                current_answer_count
                > before_answer_count
            )

            new_answer_done = (
                current_done_count
                > before_done_count
            )

            if new_answer_created and new_answer_done:
                print()
                print("[DONE] 检测到新回答完成")
                break

            page.wait_for_timeout(1000)

        else:
            print()
            print("[TIMEOUT] 60 秒内没有检测到完成")

        print()
        print("=" * 90)
        print("INVESTIGATION COMPLETE")
        print("=" * 90)


if __name__ == "__main__":
    main()