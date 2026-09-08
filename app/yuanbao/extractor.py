from __future__ import annotations

from urllib.parse import urlparse

from playwright.sync_api import Page

from app.yuanbao.selectors import (
    REFERENCE_CARD_SELECTOR,
    REFERENCE_DESC_SELECTOR,
    REFERENCE_ITEM_SELECTOR,
    REFERENCE_SOURCE_SELECTOR,
    REFERENCE_TITLE_SELECTOR,
)

from app.yuanbao.source import YuanbaoSource


class YuanbaoSourceExtractor:

    def __init__(
            self,
            page: Page,
    ) -> None:
        self.page = page

    def extract(
            self,
    ) -> list[YuanbaoSource]:

        items = self.page.locator(
            REFERENCE_ITEM_SELECTOR
        )

        sources: list[YuanbaoSource] = []

        for index in range(
                items.count()
        ):
            item = items.nth(index)

            card = item.locator(
                REFERENCE_CARD_SELECTOR
            ).first

            if card.count() == 0:
                continue

            url = (
                    card.get_attribute(
                        "data-url"
                    )
                    or item.get_attribute(
                        "dt-ext6"
                    )
                    or ""
            ).strip()

            source_node = item.locator(
                REFERENCE_SOURCE_SELECTOR
            ).first

            title_node = item.locator(
                REFERENCE_TITLE_SELECTOR
            ).first

            desc_node = item.locator(
                REFERENCE_DESC_SELECTOR
            ).first

            source = (
                source_node.inner_text().strip()
                if source_node.count()
                else ""
            )

            title = (
                title_node.inner_text().strip()
                if title_node.count()
                else ""
            )

            description = (
                desc_node.inner_text().strip()
                if desc_node.count()
                else ""
            )

            domain = ""

            if url:
                domain = urlparse(
                    url
                ).netloc

            sources.append(
                YuanbaoSource(
                    index=index + 1,
                    source=source,
                    title=title,
                    description=description,
                    url=url,
                    domain=domain,
                )
            )

        return sources