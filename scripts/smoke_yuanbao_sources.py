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

        print("=" * 90)
        print("YUANBAO SOURCES SMOKE TEST")
        print("=" * 90)

        client.new_chat()

        client.set_profile(
            model=YuanbaoModel.HY3,
            mode=YuanbaoMode.EXPERT,
        )

        answer = client.ask(
            QUESTION
        )

        sources = client.get_sources()

        print(
            f"[ANSWER LENGTH] {len(answer)}"
        )

        print(
            f"[SOURCE COUNT] {len(sources)}"
        )

        for source in sources:
            print("-" * 90)
            print(
                f"[{source.index}] "
                f"{source.source}"
            )
            print(
                f"TITLE: {source.title}"
            )
            print(
                f"URL:   {source.url}"
            )
            print(
                f"DESC:  {source.description}"
            )

        if not sources:
            raise RuntimeError(
                "没有采集到腾讯元宝信源"
            )

        if any(
                not source.url
                for source in sources
        ):
            raise RuntimeError(
                "存在缺少 URL 的信源"
            )

        print()
        print("=" * 90)
        print("SOURCE STATUS: PASS")
        print("=" * 90)


if __name__ == "__main__":
    main()
