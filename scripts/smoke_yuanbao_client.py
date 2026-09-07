from playwright.sync_api import sync_playwright

from app.browser.cdp import connect_cdp
from app.core.config import get_settings
from app.yuanbao.client import YuanbaoClient


TEST_QUESTION = (
    "请只回答这句话：腾讯元宝 GEO 采集测试成功"
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

        client = YuanbaoClient(
            page=page,
            answer_timeout_seconds=60,
        )

        print("=" * 80)
        print("YUANBAO CLIENT SMOKE TEST")
        print("=" * 80)

        print(f"[URL]      {page.url}")
        print(f"[QUESTION] {TEST_QUESTION}")

        answer = client.ask(TEST_QUESTION)

        print(f"[ANSWER]   {answer}")
        print(f"[URL]      {page.url}")

        print()
        print("=" * 80)
        print("CLIENT STATUS: PASS")
        print("=" * 80)


if __name__ == "__main__":
    main()