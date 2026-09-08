from __future__ import annotations

import json
from pathlib import Path

from app.yuanbao.result import YuanbaoCollectionResult
from app.yuanbao.checksum import generate_checksums


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

    def _save_answers(
            self,
            results,
            path: Path,
    ):

        data = []

        for result in results:
            data.append(
                {
                    "question": result.question,
                    "answer": result.answer,
                    "model": result.model,
                    "mode": result.mode,
                    "conversation_url": result.conversation_url,
                    "status": result.status,
                }
            )

        self._write_json(path, data)

    def _save_sources(
            self,
            results,
            path: Path,
    ):

        data = []

        for result in results:
            data.append(
                {
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

        self._write_json(path, data)

    def _save_manifest(
            self,
            results,
            path: Path,
    ):

        success = sum(
            1
            for result in results
            if result.status == "success"
        )

        failed = len(results) - success

        manifest = {
            "platform": "yuanbao",
            "total": len(results),
            "success": success,
            "failed": failed,
        }

        self._write_json(path, manifest)

    def _write_json(
            self,
            path: Path,
            data,
    ):

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
