from playwright.sync_api import sync_playwright

from app.browser.cdp import connect_cdp
from app.core.config import get_settings

from app.yuanbao.client import YuanbaoClient
from app.yuanbao.types import (
    YuanbaoMode,
    YuanbaoModel,
)

QUESTION = (
    "鸿茅药酒是正规药品吗？"
    "请基于公开网页资料回答，并附参考来源。"
)


def main():
    settings = get_settings()

    with sync_playwright() as playwright:
        browser = connect_cdp(
            playwright,
            settings.cdp_url,
        )

        page = browser.contexts[0].pages[0]

        client = YuanbaoClient(
            page=page,
            answer_timeout_seconds=180,
        )

        result = client.collect(
            question=QUESTION,
            model=YuanbaoModel.HY3,
            mode=YuanbaoMode.EXPERT,
        )

        print("=" * 90)
        print(
            "YUANBAO PIPELINE TEST"
        )
        print("=" * 90)

        print()

        print(
            "[QUESTION]"
        )
        print(
            result.question
        )

        print()

        print(
            "[ANSWER LENGTH]"
        )
        print(
            len(result.answer)
        )

        print()

        print(
            "[MODEL]"
        )
        print(
            result.model
        )

        print()

        print(
            "[MODE]"
        )
        print(
            result.mode
        )

        print()

        print(
            "[URL]"
        )
        print(
            result.conversation_url
        )

        print()

        print(
            "[SOURCE COUNT]"
        )
        print(
            len(result.sources)
        )

        for source in result.sources:
            print("-" * 80)

            print(
                source.source
            )

            print(
                source.title
            )

            print(
                source.url
            )

            print(
                source.domain
            )

        print()

        print(
            "PIPELINE STATUS: PASS"
        )


if __name__ == "__main__":
    main()
