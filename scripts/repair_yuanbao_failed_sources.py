from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime
from pathlib import Path

from playwright.sync_api import sync_playwright

from app.browser.cdp import (
    connect_cdp,
    find_page_by_url,
)
from app.core.config import get_settings
from app.yuanbao.checkpoint import YuanbaoCheckpointStore
from app.yuanbao.client import YuanbaoClient
from app.yuanbao.exporter import YuanbaoExporter
from app.yuanbao.geo_contract import (
    build_task_id,
    to_geo_mode,
)
from app.yuanbao.loader import load_questions
from app.yuanbao.packager import create_package
from app.yuanbao.result import utc_now_iso
from app.yuanbao.runner import (
    YuanbaoBatchRunner,
    build_geo_tasks,
)


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "只重新采集回答成功、"
            "但来源采集失败的腾讯元宝任务"
        )
    )

    parser.add_argument(
        "--batch-id",
        required=True,
    )

    parser.add_argument(
        "--checkpoint-root",
        default="output/checkpoints",
    )

    parser.add_argument(
        "--input",
        default="input/questions.csv",
    )

    parser.add_argument(
        "--output-dir",
        default="output/test_batch",
    )

    parser.add_argument(
        "--package",
        default="output/yuanbao_geo_package.zip",
    )

    parser.add_argument(
        "--list-only",
        action="store_true",
        help="只列出待修复任务，不执行网页采集",
    )

    return parser.parse_args()


def prepare_task_ids(
        tasks,
        batch_id: str,
) -> None:
    for task in tasks:
        mode_code = to_geo_mode(
            task.mode
        )

        task.task_id = build_task_id(
            batch_id=batch_id,
            question_id=task.question_id,
            mode_code=mode_code,
        )


def load_all_results(
        store: YuanbaoCheckpointStore,
        tasks,
):
    results = []

    for task in tasks:
        result = store.load_result(
            task.task_id
        )

        if result is None:
            raise RuntimeError(
                "Checkpoint 缺少任务结果："
                f"{task.task_id}"
            )

        results.append(result)

    return results


def main() -> None:
    args = parse_args()

    checkpoint_root = Path(
        args.checkpoint_root
    )

    store = YuanbaoCheckpointStore(
        checkpoint_root,
        args.batch_id,
    )

    if not store.meta_path.is_file():
        raise FileNotFoundError(
            f"找不到 batch_meta.json："
            f"{store.meta_path}"
        )

    meta = json.loads(
        store.meta_path.read_text(
            encoding="utf-8",
        )
    )

    questions = load_questions(
        args.input
    )

    tasks = build_geo_tasks(
        questions
    )

    prepare_task_ids(
        tasks,
        args.batch_id,
    )

    repair_tasks = []

    for task in tasks:
        cached = store.load_result(
            task.task_id
        )

        if cached is None:
            continue

        needs_source_repair = (
            cached.status == "success"
            and cached.is_complete
            and cached.source_collection_status
            == "failed"
        )

        if needs_source_repair:
            repair_tasks.append(
                (
                    task,
                    cached,
                )
            )

    print("=" * 80)
    print("YUANBAO SOURCE REPAIR")
    print("=" * 80)

    print(
        f"[BATCH] {args.batch_id}"
    )

    print(
        f"[TOTAL TASKS] {len(tasks)}"
    )

    print(
        f"[REPAIR TASKS] "
        f"{len(repair_tasks)}"
    )

    print()

    for index, (
            task,
            cached,
    ) in enumerate(
            repair_tasks,
            start=1,
    ):
        print("-" * 80)
        print(
            f"[{index}/"
            f"{len(repair_tasks)}]"
        )
        print(
            f"TASK_ID: {task.task_id}"
        )
        print(
            f"MODE: {task.mode.value}"
        )
        print(
            f"QUESTION: {task.question}"
        )
        print(
            "SOURCE STATUS: "
            f"{cached.source_collection_status}"
        )

    if not repair_tasks:
        print()
        print(
            "[PASS] 没有需要修复的来源失败任务"
        )
        return

    if args.list_only:
        print()
        print(
            "[LIST ONLY] "
            "未执行任何网页采集，"
            "Checkpoint 未修改。"
        )
        return

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    backup_dir = (
        store.batch_dir
        / f"repair_backup_{timestamp}"
    )

    backup_dir.mkdir(
        parents=True,
        exist_ok=False,
    )

    print()
    print(
        f"[BACKUP] {backup_dir}"
    )

    for task, _ in repair_tasks:
        source_path = (
            store.results_dir
            / f"{task.task_id}.json"
        )

        shutil.copy2(
            source_path,
            backup_dir / source_path.name,
        )

    settings = get_settings()

    repaired_count = 0

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
            f"[PAGE] {page.url}"
        )

        client = YuanbaoClient(
            page=page,
            answer_timeout_seconds=180,
        )

        runner = YuanbaoBatchRunner(
            client=client,
            batch_id=args.batch_id,
            product=meta.get(
                "product",
                "鸿茅药酒",
            ),
            checkpoint_store=store,
        )

        for index, (
                task,
                old_result,
        ) in enumerate(
                repair_tasks,
                start=1,
        ):
            print()
            print("=" * 80)
            print(
                f"[REPAIR {index}/"
                f"{len(repair_tasks)}]"
            )
            print(
                task.question
            )
            print(
                f"[MODE] "
                f"{task.mode.value}"
            )

            new_result = (
                runner
                .run_task_with_retry(
                    task
                )
            )

            source_ok = (
                new_result.status
                == "success"
                and
                new_result.is_complete
                and
                new_result
                .source_collection_status
                == "success"
            )

            if not source_ok:
                print(
                    "[REPAIR FAILED] "
                    "新结果来源仍未采集成功"
                )

                print(
                    "[KEEP OLD] "
                    "原 Checkpoint 不覆盖"
                )

                if new_result.source_error:
                    print(
                        "[SOURCE ERROR] "
                        f"{new_result.source_error}"
                    )

                continue

            store.save_result(
                new_result
            )

            repaired_count += 1

            print(
                "[REPAIR PASS] "
                f"来源数："
                f"{new_result.source_count_raw}"
            )

    all_results = load_all_results(
        store,
        tasks,
    )

    remaining_failed_sources = [
        result
        for result in all_results
        if (
            result.status == "success"
            and result.is_complete
            and result.source_collection_status
            == "failed"
        )
    ]

    print()
    print("=" * 80)
    print("REPAIR RESULT")
    print("=" * 80)

    print(
        f"REPAIRED: {repaired_count}"
    )

    print(
        "REMAINING SOURCE FAILED: "
        f"{len(remaining_failed_sources)}"
    )

    if remaining_failed_sources:
        print()
        print(
            "[INCOMPLETE] "
            "仍存在来源失败任务。"
        )

        print(
            "原始 Checkpoint 备份已保留，"
            "本次不会重新生成最终 ZIP。"
        )

        raise SystemExit(4)

    finished_at = utc_now_iso()

    store.mark_completed(
        results=all_results,
        finished_at=finished_at,
    )

    zip_path = Path(
        args.package
    )

    if zip_path.is_file():
        old_zip_backup = (
            zip_path.parent
            / (
                f"{zip_path.stem}"
                f"_before_repair_"
                f"{timestamp}"
                f"{zip_path.suffix}"
            )
        )

        shutil.copy2(
            zip_path,
            old_zip_backup,
        )

        print(
            "[OLD ZIP BACKUP] "
            f"{old_zip_backup}"
        )

    exporter = YuanbaoExporter()

    exporter.export(
        all_results,
        args.output_dir,
        started_at=meta.get(
            "started_at",
            "",
        ),
        finished_at=finished_at,
    )

    new_zip = create_package(
        source_dir=args.output_dir,
        zip_path=args.package,
    )

    print()
    print("=" * 80)
    print("SOURCE REPAIR COMPLETE")
    print("=" * 80)

    print(
        f"[TASKS] {len(all_results)}"
    )

    print(
        "[SOURCE FAILED] 0"
    )

    print(
        f"[ZIP] {new_zip}"
    )


if __name__ == "__main__":
    main()
