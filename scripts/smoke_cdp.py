from playwright.sync_api import sync_playwright

from app.browser.cdp import connect_cdp
from app.core.config import get_settings


def main() -> None:
    settings = get_settings()

    with sync_playwright() as playwright:
        browser = connect_cdp(
            playwright=playwright,
            cdp_url=settings.cdp_url,
        )

        print("=" * 60)
        print("YUANBAO CDP SMOKE TEST")
        print("=" * 60)

        contexts = browser.contexts

        print(f"[CDP] contexts: {len(contexts)}")

        if not contexts:
            raise RuntimeError("没有找到浏览器 Context")

        context = contexts[0]

        pages = context.pages

        print(f"[CDP] pages: {len(pages)}")

        for index, page in enumerate(pages, start=1):
            print("-" * 60)
            print(f"[PAGE {index}]")
            print(f"TITLE: {page.title()}")
            print(f"URL:   {page.url}")

        print("-" * 60)
        print("CDP STATUS: PASS")


if __name__ == "__main__":
    main()
