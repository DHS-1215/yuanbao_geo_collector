from __future__ import annotations

import json
from pathlib import Path

from app.yuanbao.checksum import generate_checksums
from app.yuanbao.geo_contract import (
    YUANBAO_PLATFORM_CODE,
    build_answer_id,
    build_occurrence_id,
)
from app.yuanbao.result import YuanbaoCollectionResult


class YuanbaoExporter:

    def export(
            self,
            results: list[YuanbaoCollectionResult],
            output_dir: str,
    ) -> None:

        output = Path(output_dir)

        output.mkdir(
            parents=True,
            exist_ok=True,
        )

        # GEO v1 标准输出
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

        # 旧版输出暂时保留，
        # 后续 W9 阶段再逐步替换
        self._save_answers(
            results,
            output / "answers.json",
        )

        self._save_sources(
            results,
            output / "sources.json",
        )

        self._save_manifest(
            results,
            output / "manifest.json",
        )

        checksum_files = [
            output / "answers.json",
            output / "sources.json",
            output / "manifest.json",
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

        product = (
            results[0].product
            if results
            else ""
        )

        manifest = {
            "batch_id": batch_id,
            "platform": "yuanbao",
            "product": product,
            "total": len(results),
            "success": success,
            "failed": failed,
        }

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
