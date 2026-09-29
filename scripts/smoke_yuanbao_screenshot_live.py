from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from zipfile import ZipFile

from playwright.sync_api import sync_playwright

from app.browser.cdp import (
    connect_cdp,
    find_page_by_url,
)
from app.core.config import get_settings

from app.yuanbao.client import YuanbaoClient
from app.yuanbao.exporter import YuanbaoExporter
from app.yuanbao.loader import load_questions
from app.yuanbao.packager import create_package
from app.yuanbao.runner import (
    YuanbaoBatchRunner,
    build_geo_tasks,
)


def main() -> None:
    settings = get_settings()

    batch_id = datetime.now().strftime(
        "batch_screenshot_smoke_%Y%m%d_%H%M%S"
    )

    output_dir = Path(
        "output/screenshot_smoke"
    )

    zip_path = Path(
        "output/yuanbao_screenshot_smoke.zip"
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
            f"[PAGE]  {page.url}"
        )

        client = YuanbaoClient(
            page=page,
            answer_timeout_seconds=180,
        )

        questions = load_questions(
            "input/questions.csv"
        )

        if not questions:
            raise RuntimeError(
                "questions.csv is empty"
            )

        # Only one full question:
        # quick + expert = 2 tasks.
        tasks = build_geo_tasks(
            questions[:1]
        )

        print(
            f"[BATCH] {batch_id}"
        )

        print(
            f"[QUESTION] "
            f"{questions[0].question}"
        )

        print(
            f"[TASKS] {len(tasks)}"
        )

        runner = YuanbaoBatchRunner(
            client=client,
            batch_id=batch_id,
            product="鸿茅药酒",
        )

        results = runner.run(
            tasks
        )

        failed = [
            result
            for result in results
            if (
                result.status != "success"
                or not result.is_complete
            )
        ]

        if failed:
            for result in failed:
                print(
                    "[FAILED]",
                    result.task_id,
                    result.error,
                )

            raise SystemExit(3)

        exporter = YuanbaoExporter()

        exporter.export(
            results,
            str(output_dir),
            started_at=runner.started_at,
            finished_at=runner.finished_at,
        )

        create_package(
            source_dir=output_dir,
            zip_path=zip_path,
        )

    print()
    print("=" * 80)
    print("LIVE SCREENSHOT SMOKE RESULT")
    print("=" * 80)

    for result in results:
        print(
            "[TASK]",
            result.task_id,
        )

        print(
            "[SCREENSHOT SOURCE]",
            result.screenshot_path,
        )

        print(
            "[SHA256]",
            result.screenshot_sha256,
        )

        print(
            "[SIZE]",
            result.screenshot_size_bytes,
        )

        print(
            "[DIMENSIONS]",
            f"{result.screenshot_width}"
            f"x{result.screenshot_height}",
        )

    answers = [
        json.loads(line)
        for line in (
            output_dir
            / "answers.jsonl"
        ).read_text(
            encoding="utf-8"
        ).splitlines()
        if line.strip()
    ]

    print()
    print("[ANSWER REFERENCES]")

    for row in answers:
        print(
            row["task_id"],
            "->",
            row.get(
                "screenshot_path"
            ),
        )

    with ZipFile(
            zip_path,
            "r",
    ) as zip_file:
        screenshot_names = [
            name
            for name in zip_file.namelist()
            if name.startswith(
                "screenshots/"
            )
        ]

    print()
    print(
        "[ZIP]",
        zip_path.resolve(),
    )

    print(
        "[ZIP SCREENSHOTS]",
        len(screenshot_names),
    )

    for name in screenshot_names:
        print(
            "-",
            name,
        )

    print()
    print("LIVE SCREENSHOT SMOKE: PASS")


if __name__ == "__main__":
    main()
