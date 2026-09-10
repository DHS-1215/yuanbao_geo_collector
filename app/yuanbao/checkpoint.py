from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from app.yuanbao.result import (
    YuanbaoCollectionResult,
    utc_now_iso,
)
from app.yuanbao.source import YuanbaoSource

RESUMABLE_BATCH_STATUSES = {
    "running",
    "interrupted",
    "completed_with_failures",
}


class YuanbaoCheckpointStore:

    def __init__(
            self,
            root_dir: str | Path,
            batch_id: str,
    ) -> None:
        self.root_dir = Path(root_dir)

        self.batch_id = batch_id

        self.batch_dir = (
                self.root_dir
                / batch_id
        )

        self.results_dir = (
                self.batch_dir
                / "results"
        )

        self.meta_path = (
                self.batch_dir
                / "batch_meta.json"
        )

        self.active_path = (
                self.root_dir
                / "active_batch.json"
        )

    @classmethod
    def resolve_batch_id(
            cls,
            root_dir: str | Path,
            new_batch_id: str,
            *,
            force_new: bool = False,
    ) -> tuple[str, bool]:

        root = Path(root_dir)

        root.mkdir(
            parents=True,
            exist_ok=True,
        )

        active_path = (
                root
                / "active_batch.json"
        )

        if (
                not force_new
                and active_path.is_file()
        ):
            try:
                active = cls._read_json_file(
                    active_path
                )

                batch_id = (
                    active
                    .get("batch_id", "")
                    .strip()
                )

                if batch_id:
                    meta_path = (
                            root
                            / batch_id
                            / "batch_meta.json"
                    )

                    if meta_path.is_file():
                        meta = (
                            cls._read_json_file(
                                meta_path
                            )
                        )

                        status = (
                            meta.get(
                                "status",
                                ""
                            )
                        )

                        if (
                                status
                                in RESUMABLE_BATCH_STATUSES
                        ):
                            return (
                                batch_id,
                                True,
                            )

            except (
                    OSError,
                    ValueError,
                    json.JSONDecodeError,
            ):
                pass

        return (
            new_batch_id,
            False,
        )

    def initialize(
            self,
            *,
            product: str,
            planned_count: int,
    ) -> str:

        self.results_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        if self.meta_path.is_file():
            meta = self._read_json_file(
                self.meta_path
            )

            existing_product = (
                meta.get(
                    "product",
                    ""
                )
            )

            if (
                    existing_product
                    and existing_product
                    != product
            ):
                raise ValueError(
                    "Checkpoint 产品不一致："
                    f"{existing_product} != "
                    f"{product}"
                )

            started_at = (
                    meta.get(
                        "started_at",
                        ""
                    )
                    or utc_now_iso()
            )

        else:
            started_at = utc_now_iso()

            meta = {
                "batch_id": self.batch_id,
                "product": product,
                "started_at": started_at,
                "finished_at": "",
                "status": "running",
                "planned_count": (
                    planned_count
                ),
                "completed_count": 0,
                "success_count": 0,
                "failed_count": 0,
                "updated_at": started_at,
            }

        meta["status"] = "running"

        meta["planned_count"] = (
            planned_count
        )

        meta["updated_at"] = (
            utc_now_iso()
        )

        self._write_json_atomic(
            self.meta_path,
            meta,
        )

        self._write_active_pointer()

        return started_at

    def save_result(
            self,
            result: YuanbaoCollectionResult,
    ) -> None:

        if not result.task_id:
            raise ValueError(
                "保存 checkpoint 时 "
                "task_id 不能为空"
            )

        path = (
                self.results_dir
                / f"{result.task_id}.json"
        )

        payload = asdict(
            result
        )

        self._write_json_atomic(
            path,
            payload,
        )

        self._refresh_progress()

    def load_result(
            self,
            task_id: str,
    ) -> YuanbaoCollectionResult | None:

        path = (
                self.results_dir
                / f"{task_id}.json"
        )

        if not path.is_file():
            return None

        payload = self._read_json_file(
            path
        )

        source_rows = (
            payload.pop(
                "sources",
                [],
            )
        )

        sources = [
            YuanbaoSource(
                **source
            )
            for source in source_rows
        ]

        return YuanbaoCollectionResult(
            sources=sources,
            **payload,
        )

    def mark_completed(
            self,
            *,
            results: list[
                YuanbaoCollectionResult
            ],
            finished_at: str,
    ) -> None:

        success_count = sum(
            1
            for result in results
            if (
                    result.status == "success"
                    and result.is_complete
            )
        )

        failed_count = (
                len(results)
                - success_count
        )

        status = (
            "completed"
            if failed_count == 0
            else "completed_with_failures"
        )

        self._update_meta(
            status=status,
            finished_at=finished_at,
            completed_count=len(results),
            success_count=success_count,
            failed_count=failed_count,
        )

        if status == "completed":
            self._clear_active_pointer()
        else:
            self._write_active_pointer()

    def mark_interrupted(
            self,
            *,
            finished_at: str,
    ) -> None:

        self._update_meta(
            status="interrupted",
            finished_at=finished_at,
        )

        self._write_active_pointer()

    def _refresh_progress(
            self,
    ) -> None:

        results = []

        for path in (
                self.results_dir
                        .glob("*.json")
        ):
            try:
                payload = (
                    self._read_json_file(
                        path
                    )
                )

                results.append(
                    payload
                )

            except (
                    OSError,
                    ValueError,
                    json.JSONDecodeError,
            ):
                continue

        success_count = sum(
            1
            for result in results
            if (
                    result.get("status")
                    == "success"
                    and result.get(
                "is_complete"
            )
                    is True
            )
        )

        failed_count = (
                len(results)
                - success_count
        )

        self._update_meta(
            completed_count=len(results),
            success_count=success_count,
            failed_count=failed_count,
        )

    def _update_meta(
            self,
            **changes,
    ) -> None:

        meta = (
            self._read_json_file(
                self.meta_path
            )
            if self.meta_path.is_file()
            else {
                "batch_id": self.batch_id
            }
        )

        meta.update(
            changes
        )

        meta["updated_at"] = (
            utc_now_iso()
        )

        self._write_json_atomic(
            self.meta_path,
            meta,
        )

    def _write_active_pointer(
            self,
    ) -> None:

        self.root_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        self._write_json_atomic(
            self.active_path,
            {
                "batch_id": (
                    self.batch_id
                )
            },
        )

    def _clear_active_pointer(
            self,
    ) -> None:

        if not self.active_path.is_file():
            return

        try:
            active = (
                self._read_json_file(
                    self.active_path
                )
            )

            if (
                    active.get("batch_id")
                    == self.batch_id
            ):
                self.active_path.unlink()

        except (
                OSError,
                ValueError,
                json.JSONDecodeError,
        ):
            pass

    @staticmethod
    def _write_json_atomic(
            path: Path,
            data,
    ) -> None:

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        temp_path = (
            path.with_suffix(
                path.suffix + ".tmp"
            )
        )

        with temp_path.open(
                "w",
                encoding="utf-8",
        ) as file:
            json.dump(
                data,
                file,
                ensure_ascii=False,
                indent=2,
            )

        temp_path.replace(
            path
        )

    @staticmethod
    def _read_json_file(
            path: Path,
    ) -> dict:

        with path.open(
                "r",
                encoding="utf-8",
        ) as file:
            data = json.load(
                file
            )

        if not isinstance(
                data,
                dict,
        ):
            raise ValueError(
                f"Checkpoint JSON "
                f"不是对象：{path}"
            )

        return data
