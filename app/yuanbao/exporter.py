from __future__ import annotations

import json
from pathlib import Path

from app.yuanbao.checksum import generate_checksums
from app.yuanbao.geo_contract import (
    COLLECTOR_VERSION,
    DEFAULT_PRODUCT_ID,
    DEFAULT_PRODUCT_NAME,
    GEO_BATCH_VERSION,
    GEO_SCHEMA_VERSION,
    YUANBAO_PLATFORM_CODE,
    YUANBAO_PLATFORM_NAME,
    build_answer_id,
    build_occurrence_id,
)
from app.yuanbao.result import YuanbaoCollectionResult


class YuanbaoExporter:

    def export(
            self,
            results: list[YuanbaoCollectionResult],
            output_dir: str,
            started_at: str = "",
            finished_at: str = "",
    ) -> None:

        output = Path(output_dir)

        output.mkdir(
            parents=True,
            exist_ok=True,
        )

        # 清理旧版中间产物，避免标准目录中
        # 残留 answers.json / sources.json。
        for legacy_filename in (
                "answers.json",
                "sources.json",
        ):
            legacy_path = (
                    output
                    / legacy_filename
            )

            if legacy_path.exists():
                legacy_path.unlink()

        # GEO v1 标准数据文件
        self._save_tasks_jsonl(
            results,
            output / "tasks.jsonl",
        )

        self._save_answers_jsonl(
            results,
            output / "answers.jsonl",
        )

        self._save_sources_jsonl(
            results,
            output / "sources.jsonl",
        )

        self._save_manifest(
            results,
            output / "manifest.json",
            started_at=started_at,
            finished_at=finished_at,
        )

        # checksums.json 不计算自身 checksum。
        checksum_files = [
            output / "manifest.json",
            output / "tasks.jsonl",
            output / "answers.jsonl",
            output / "sources.jsonl",
        ]

        checksums = generate_checksums(
            checksum_files
        )

        self._write_json(
            output / "checksums.json",
            checksums,
        )

    def _save_tasks_jsonl(
            self,
            results: list[YuanbaoCollectionResult],
            path: Path,
    ) -> None:

        rows = []

        for result in results:
            rows.append(
                {
                    "task_id": result.task_id,
                    "batch_id": result.batch_id,
                    "platform_code": YUANBAO_PLATFORM_CODE,
                    "question_id": result.question_id,
                    "question": result.question,
                    "mode_code": result.mode_code,
                    "task_status": result.status,
                    "error_code": None,
                    "error_message": (
                            result.error
                            or None
                    ),
                }
            )

        self._write_jsonl(
            path,
            rows,
        )

    def _save_answers_jsonl(
            self,
            results: list[YuanbaoCollectionResult],
            path: Path,
    ) -> None:

        rows = []

        for result in results:
            answer_id = build_answer_id(
                batch_id=result.batch_id,
                task_id=result.task_id,
            )

            platform_meta = {
                "model": result.model,
                "raw_mode": result.mode,
                "conversation_url": result.conversation_url,
            }

            if result.source_error:
                platform_meta[
                    "source_error"
                ] = result.source_error

            rows.append(
                {
                    "answer_id": answer_id,
                    "task_id": result.task_id,
                    "question_id": result.question_id,
                    "mode_code": result.mode_code,
                    "question_text": result.question,
                    "answer_text_raw": result.answer,
                    "answer_text_clean": (
                        result.answer.strip()
                        if result.answer
                        else ""
                    ),
                    "acquisition_status": (
                        result.acquisition_status
                    ),
                    "validation_status": (
                        result.validation_status
                    ),
                    "is_complete": (
                        result.is_complete
                    ),
                    "source_collection_status": (
                        result.source_collection_status
                    ),
                    "source_count_raw": (
                        result.source_count_raw
                    ),
                    "screenshot_path": None,
                    "platform_meta_json": (
                        platform_meta
                    ),
                    "collected_at": (
                            result.collected_at
                            or None
                    ),
                    "batch_id": (
                        result.batch_id
                    ),
                    "platform_code": (
                        YUANBAO_PLATFORM_CODE
                    ),
                }
            )

        self._write_jsonl(
            path,
            rows,
        )

    def _save_sources_jsonl(
            self,
            results: list[YuanbaoCollectionResult],
            path: Path,
    ) -> None:

        rows = []

        for result in results:
            answer_id = build_answer_id(
                batch_id=result.batch_id,
                task_id=result.task_id,
            )

            seen_urls: set[str] = set()

            for source in result.sources:
                source_url_raw = (
                    source.url.strip()
                )

                # 中央标准 source_url_raw
                # 不能为空。
                if not source_url_raw:
                    continue

                is_duplicate = (
                        source_url_raw
                        in seen_urls
                )

                seen_urls.add(
                    source_url_raw
                )

                source_order = (
                    source.index
                )

                occurrence_id = (
                    build_occurrence_id(
                        batch_id=result.batch_id,
                        answer_id=answer_id,
                        source_order=source_order,
                        source_url_raw=source_url_raw,
                    )
                )

                rows.append(
                    {
                        "answer_id": answer_id,
                        "source_order": source_order,
                        "source_url_raw": (
                            source_url_raw
                        ),
                        "source_title_raw": (
                                source.title
                                or None
                        ),
                        "source_site_name_raw": (
                                source.source
                                or None
                        ),
                        "source_snippet": (
                                source.description
                                or None
                        ),
                        "is_duplicate_in_answer": (
                            is_duplicate
                        ),
                        "occurrence_id": (
                            occurrence_id
                        ),
                    }
                )

        self._write_jsonl(
            path,
            rows,
        )

    def _write_jsonl(
            self,
            path: Path,
            rows,
    ) -> None:

        with open(
                path,
                "w",
                encoding="utf-8",
        ) as f:
            for row in rows:
                f.write(
                    json.dumps(
                        row,
                        ensure_ascii=False,
                    )
                )
                f.write("\n")

    def _save_answers(
            self,
            results: list[YuanbaoCollectionResult],
            path: Path,
    ) -> None:

        data = []

        for result in results:
            data.append(
                {
                    "batch_id": result.batch_id,
                    "task_id": result.task_id,
                    "platform": result.platform,
                    "product": result.product,
                    "question": result.question,
                    "answer": result.answer,
                    "model": result.model,
                    "mode": result.mode,
                    "conversation_url": result.conversation_url,
                    "status": result.status,
                }
            )

        self._write_json(
            path,
            data,
        )

    def _save_sources(
            self,
            results: list[YuanbaoCollectionResult],
            path: Path,
    ) -> None:

        data = []

        for result in results:
            data.append(
                {
                    "batch_id": result.batch_id,
                    "task_id": result.task_id,
                    "platform": result.platform,
                    "product": result.product,
                    "question": result.question,
                    "sources": [
                        {
                            "source": source.source,
                            "title": source.title,
                            "url": source.url,
                            "domain": source.domain,
                            "description": source.description,
                        }
                        for source in result.sources
                    ],
                }
            )

        self._write_json(
            path,
            data,
        )

    def _save_manifest(
            self,
            results: list[YuanbaoCollectionResult],
            path: Path,
            started_at: str = "",
            finished_at: str = "",
    ) -> None:

        success = sum(
            1
            for result in results
            if result.status == "success"
        )

        failed = (
                len(results)
                - success
        )

        batch_id = (
            results[0].batch_id
            if results
            else ""
        )

        collection_modes = sorted(
            {
                result.mode_code
                for result in results
                if result.mode_code
            }
        )

        source_count = sum(
            1
            for result in results
            for source in result.sources
            if source.url.strip()
        )

        manifest = {
            "schema_version": (
                GEO_SCHEMA_VERSION
            ),
            "geo_batch_version": (
                GEO_BATCH_VERSION
            ),

            "platform_code": (
                YUANBAO_PLATFORM_CODE
            ),
            "platform_name": (
                YUANBAO_PLATFORM_NAME
            ),

            "product_id": (
                DEFAULT_PRODUCT_ID
            ),
            "product_name": (
                DEFAULT_PRODUCT_NAME
            ),

            "batch_id": batch_id,

            "collector_version": (
                COLLECTOR_VERSION
            ),

            "capabilities": {
                "supports_sources": True,
                "supports_multiple_modes": True,
                "supports_screenshot": False,
            },

            "status": (
                "PASS"
                if failed == 0
                else "PASS_WITH_WARNINGS"
            ),

            "task_count": len(results),
            "answer_count": len(results),
            "source_count": source_count,

            "success_tasks": success,
            "failed_tasks": failed,

            "collection_modes": (
                collection_modes
            ),
        }

        if started_at:
            manifest[
                "started_at"
            ] = started_at

        if finished_at:
            manifest[
                "finished_at"
            ] = finished_at

        self._write_json(
            path,
            manifest,
        )

    def _write_json(
            self,
            path: Path,
            data,
    ) -> None:

        with open(
                path,
                "w",
                encoding="utf-8",
        ) as f:
            json.dump(
                data,
                f,
                ensure_ascii=False,
                indent=2,
            )
