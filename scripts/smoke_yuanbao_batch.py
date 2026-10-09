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
    YuanbaoSessionRotate,
    build_geo_tasks,
)
from app.yuanbao.checkpoint import (
    YuanbaoCheckpointStore,
)
from app.yuanbao.exporter import YuanbaoExporter
from app.yuanbao.geo_contract import (
    DEFAULT_PRODUCT_ID,
    resolve_product,
)


def main():
    args = parse_args()

    settings = get_settings()

    product_id, product = resolve_product(
        args.product_id
    )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    new_batch_id = (
        f"batch_{product_id}_{timestamp}"
    )

    checkpoint_root = (
        args.checkpoint_root
        or f"output/checkpoints/{product_id}"
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
            args.input_csv
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

        print(
            f"[PRODUCT ID] {product_id}"
        )

        print(
            f"[INPUT]   {args.input_csv}"
        )

        print(
            f"[CHECKPOINT ROOT] "
            f"{checkpoint_root}"
        )

        print()

        try:
            results = runner.run(
                tasks
            )

        except YuanbaoSessionRotate as exc:
            print()
            print("=" * 80)
            print("SESSION ROTATE")
            print("=" * 80)
            print(str(exc))
            print(
                "[CHECKPOINT] "
                "Current batch remains resumable."
            )
            print(
                "[NEXT] "
                "Start a new Chrome session "
                "and resume this batch."
            )

            raise SystemExit(4)

        exporter = YuanbaoExporter(
            product_id=product_id,
            product_name=product,
        )

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

        failed = (
                len(results)
                - success
        )

        print(
            f"FAILED: {failed}"
        )

        if failed > 0:
            print()
            print(
                "[BATCH INCOMPLETE] "
                "存在未成功任务，"
                "Checkpoint 已保留。"
            )

            raise SystemExit(3)


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--new-batch",
        action="store_true",
        help="忽略未完成批次，强制开始新批次",
    )

    parser.add_argument(
        "--product-id",
        default=DEFAULT_PRODUCT_ID,
    )

    parser.add_argument(
        "--input-csv",
        default="input/questions.csv",
    )

    parser.add_argument(
        "--checkpoint-root",
        default="",
    )

    return parser.parse_args()


if __name__ == "__main__":
    main()
