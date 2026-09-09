from playwright.sync_api import sync_playwright
from datetime import datetime

from app.browser.cdp import connect_cdp
from app.core.config import get_settings

from app.yuanbao.client import YuanbaoClient
from app.yuanbao.loader import load_questions
from app.yuanbao.runner import (
    YuanbaoBatchRunner,
    build_geo_tasks
)
from app.yuanbao.exporter import YuanbaoExporter


def main():
    settings = get_settings()

    batch_id = datetime.now().strftime(
        "batch_%Y%m%d_%H%M%S"
    )

    product = "鸿茅药酒"

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

        questions = load_questions(
            "input/questions.csv"
        )

        tasks = build_geo_tasks(
            questions
        )

        runner = YuanbaoBatchRunner(
            client=client,
            batch_id=batch_id,
            product=product,
        )

        print(f"[BATCH]   {batch_id}")
        print(f"[PRODUCT] {product}")
        print()

        results = runner.run(
            tasks
        )

        exporter = YuanbaoExporter()

        exporter.export(
            results,
            "output/test_batch",
            started_at=runner.started_at,
            finished_at=runner.finished_at,
        )

        print()
        print("=" * 80)
        print("BATCH RESULT")
        print("=" * 80)

        success = sum(
            1
            for r in results
            if r.status == "success"
        )

        print(
            f"TOTAL: {len(results)}"
        )

        print(
            f"SUCCESS: {success}"
        )


if __name__ == "__main__":
    main()
