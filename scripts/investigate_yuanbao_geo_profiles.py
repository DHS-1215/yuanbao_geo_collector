from __future__ import annotations

from playwright.sync_api import sync_playwright

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

PROFILES = [
    (
        YuanbaoModel.HY3,
        YuanbaoMode.QUICK,
    ),
    (
        YuanbaoModel.HY3,
        YuanbaoMode.THINKING,
    ),
    (
        YuanbaoModel.HY3,
        YuanbaoMode.EXPERT,
    ),
    (
        YuanbaoModel.DEEPSEEK,
        YuanbaoMode.THINKING,
    ),
    (
        YuanbaoModel.HY4_PREVIEW,
        YuanbaoMode.EXPERT,
    ),
]


def inspect_latest_answer(page) -> None:
    answers = page.locator(
        ANSWER_SELECTOR
    )

    if answers.count() == 0:
        print("[DOM] 没有找到回答节点")
        return

    latest = answers.last

    result = latest.evaluate(
        """
        (answer) => {
            const root =
                answer.closest(
                    '.agent-chat__conv--ai__speech_show'
                ) || answer.parentElement;

            const links = Array.from(
                root.querySelectorAll('a')
            ).map((el) => ({
                text:
                    (
                        el.innerText
                        || el.textContent
                        || ''
                    ).trim(),
                href: el.href || '',
                title:
                    el.getAttribute('title'),
                ariaLabel:
                    el.getAttribute('aria-label'),
                className:
                    typeof el.className === 'string'
                        ? el.className
                        : '',
            }));

            const controls = Array.from(
                root.querySelectorAll(
                    'button, [aria-label]'
                )
            ).map((el) => ({
                tag: el.tagName,
                text:
                    (
                        el.innerText
                        || el.textContent
                        || ''
                    ).trim(),
                ariaLabel:
                    el.getAttribute('aria-label'),
                title:
                    el.getAttribute('title'),
                className:
                    typeof el.className === 'string'
                        ? el.className
                        : '',
            }));

            return {
                rootText:
                    (
                        root.innerText
                        || root.textContent
                        || ''
                    ).trim(),
                rootClass:
                    typeof root.className === 'string'
                        ? root.className
                        : '',
                links,
                controls,
            };
        }
        """
    )

    print()
    print("[AI ROOT CLASS]")
    print(result["rootClass"])

    print()
    print(
        f"[LINK COUNT] "
        f"{len(result['links'])}"
    )

    for index, link in enumerate(
            result["links"],
            start=1,
    ):
        print("-" * 80)
        print(f"[LINK {index}]")
        print(
            f"TEXT: "
            f"{link['text']!r}"
        )
        print(
            f"HREF: "
            f"{link['href']}"
        )
        print(
            f"TITLE: "
            f"{link['title']}"
        )
        print(
            f"ARIA: "
            f"{link['ariaLabel']}"
        )

    print()
    print(
        f"[CONTROL COUNT] "
        f"{len(result['controls'])}"
    )

    for index, control in enumerate(
            result["controls"],
            start=1,
    ):
        text = control["text"] or ""

        if len(text) > 100:
            text = text[:100] + "..."

        print("-" * 80)
        print(f"[CONTROL {index}]")
        print(
            f"TAG:  "
            f"{control['tag']}"
        )
        print(
            f"TEXT: "
            f"{text!r}"
        )
        print(
            f"ARIA: "
            f"{control['ariaLabel']}"
        )
        print(
            f"TITLE: "
            f"{control['title']}"
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
            "YUANBAO GEO PROFILE INVESTIGATION"
        )
        print("=" * 100)

        for index, (
                model,
                mode,
        ) in enumerate(
            PROFILES,
            start=1,
        ):
            print()
            print("=" * 100)
            print(
                f"[ROUND {index}] "
                f"{model.value} + {mode.value}"
            )
            print("=" * 100)

            try:
                client.new_chat()

                client.set_profile(
                    model=model,
                    mode=mode,
                )

                print(
                    f"[QUESTION] {QUESTION}"
                )

                answer = client.ask(
                    QUESTION
                )

                print()
                print("[ANSWER]")
                print(answer)

                print()
                print(
                    f"[ANSWER LENGTH] "
                    f"{len(answer)}"
                )

                print(
                    f"[URL] {page.url}"
                )

                inspect_latest_answer(page)

                print()
                print("[ROUND STATUS] PASS")

            except Exception as exc:
                print()
                print(
                    f"[ROUND STATUS] FAIL"
                )
                print(
                    f"[ERROR] "
                    f"{type(exc).__name__}: "
                    f"{exc}"
                )

        print()
        print("=" * 100)
        print(
            "GEO PROFILE INVESTIGATION COMPLETE"
        )
        print("=" * 100)


if __name__ == "__main__":
    main()
