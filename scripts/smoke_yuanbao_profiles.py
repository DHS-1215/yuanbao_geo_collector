from playwright.sync_api import sync_playwright

from app.browser.cdp import connect_cdp
from app.core.config import get_settings
from app.yuanbao.client import YuanbaoClient
from app.yuanbao.types import (
    YuanbaoMode,
    YuanbaoModel,
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
        YuanbaoMode.QUICK,
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


def main() -> None:
    settings = get_settings()

    with sync_playwright() as playwright:
        browser = connect_cdp(
            playwright=playwright,
            cdp_url=settings.cdp_url,
        )

        page = browser.contexts[0].pages[0]

        client = YuanbaoClient(page)

        print("=" * 80)
        print("YUANBAO PROFILE SMOKE TEST")
        print("=" * 80)

        for index, (
            model,
            mode,
        ) in enumerate(
            PROFILES,
            start=1,
        ):
            print()
            print("-" * 80)
            print(
                f"[ROUND {index}] "
                f"{model.value} + {mode.value}"
            )

            client.set_profile(
                model=model,
                mode=mode,
            )

            print("[STATUS] PASS")

        print()
        print("=" * 80)
        print("PROFILE STATUS: PASS")
        print("=" * 80)


if __name__ == "__main__":
    main()