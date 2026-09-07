from playwright.sync_api import Browser, Playwright


def connect_cdp(
    playwright: Playwright,
    cdp_url: str,
) -> Browser:
    browser = playwright.chromium.connect_over_cdp(cdp_url)
    return browser