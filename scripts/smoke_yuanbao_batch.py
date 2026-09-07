from playwright.sync_api import sync_playwright

from app.browser.cdp import connect_cdp
from app.core.config import get_settings

from app.yuanbao.client import YuanbaoClient
from app.yuanbao.loader import load_questions
from app.yuanbao.runner import YuanbaoBatchRunner
from app.yuanbao.exporter import YuanbaoExporter


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

        tasks = load_questions(
            "input/questions.csv"
        )

        runner = YuanbaoBatchRunner(
            client
        )

        results = runner.run(
            tasks
        )


        exporter = YuanbaoExporter()

        exporter.export(
            results,
            "output/test_batch"
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