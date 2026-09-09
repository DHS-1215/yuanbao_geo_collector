from urllib.parse import urlsplit

from playwright.sync_api import (
    Browser,
    Page,
    Playwright,
)


def connect_cdp(
        playwright: Playwright,
        cdp_url: str,
) -> Browser:
    browser = (
        playwright.chromium
        .connect_over_cdp(
            cdp_url
        )
    )

    return browser


def find_page_by_url(
        browser: Browser,
        target_url: str,
) -> Page:
    target_host = (
        urlsplit(
            target_url
        ).hostname
    )

    if not target_host:
        raise ValueError(
            f"目标 URL 无效：{target_url}"
        )

    pages: list[Page] = []

    for context in browser.contexts:
        pages.extend(
            context.pages
        )

    for page in pages:
        page_host = (
            urlsplit(
                page.url
            ).hostname
        )

        if page_host == target_host:
            return page

    current_urls = [
        page.url
        for page in pages
    ]

    raise RuntimeError(
        "未找到目标页面："
        f"{target_url}；"
        "当前浏览器页面："
        f"{current_urls}"
    )