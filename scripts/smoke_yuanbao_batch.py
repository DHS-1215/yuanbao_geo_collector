import argparse
from datetime import datetime
from playwright.sync_api import sync_playwright

from app.browser.cdp import (
    connect_cdp,
    find_page_by_url,
)
from app.core.config import get_settings

from app.yuanbao.client import YuanbaoClient
from app.yuanbao.loader import load_questions
from app.yuanbao.runner import (
    YuanbaoBatchRunner,
    build_geo_tasks
)
from app.yuanbao.checkpoint import (
    YuanbaoCheckpointStore,
)
from app.yuanbao.exporter import YuanbaoExporter


def main():
    args = parse_args()

    settings = get_settings()

    new_batch_id = datetime.now().strftime(
        "batch_%Y%m%d_%H%M%S"
    )

    checkpoint_root = (
        "output/checkpoints"
    )

    batch_id, resumed = (
        YuanbaoCheckpointStore
        .resolve_batch_id(
            checkpoint_root,
            new_batch_id,
            force_new=args.new_batch,
        )
    )

    checkpoint_store = (
        YuanbaoCheckpointStore(
            checkpoint_root,
            batch_id,
        )
    )

    product = "鸿茅药酒"

    with sync_playwright() as playwright:
        browser = connect_cdp(
            playwright,
            settings.cdp_url,
        )

        page = find_page_by_url(
            browser,
            settings.yuanbao_url,
        )

        print(
            f"[PAGE]    {page.url}"
        )

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
            checkpoint_store=(
                checkpoint_store
            ),
        )

        print(
            f"[BATCH]   {batch_id}"
        )

        print(
            f"[RESUME]  "
            f"{'YES' if resumed else 'NO'}"
        )

        print(
            f"[PRODUCT] {product}"
        )

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


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--new-batch",
        action="store_true",
        help="忽略未完成批次，强制开始新批次",
    )

    return parser.parse_args()


if __name__ == "__main__":
    main()
