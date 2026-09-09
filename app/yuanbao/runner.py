from __future__ import annotations

import random
import time
from dataclasses import dataclass

from app.yuanbao.client import YuanbaoClient
from app.yuanbao.result import (
    YuanbaoCollectionResult,
    utc_now_iso,
)
from app.yuanbao.types import (
    MODEL_MODE_COMPATIBILITY,
    YuanbaoMode,
    YuanbaoModel,
)

from app.yuanbao.geo_contract import (
    build_task_id,
    to_geo_mode,
)


@dataclass(frozen=True)
class YuanbaoQuestion:
    question_id: str
    question: str


@dataclass
class YuanbaoTask:
    question_id: str
    question: str
    model: YuanbaoModel
    mode: YuanbaoMode
    task_id: str = ""


def build_geo_tasks(
        questions: list[YuanbaoQuestion],
        model: YuanbaoModel = YuanbaoModel.HY3,
        modes: tuple[YuanbaoMode, ...] = (
                YuanbaoMode.QUICK,
                YuanbaoMode.EXPERT,
        ),
) -> list[YuanbaoTask]:
    tasks: list[YuanbaoTask] = []

    supported_modes = (
        MODEL_MODE_COMPATIBILITY[model]
    )

    for mode in modes:
        # 同时验证：
        # 1. 是否属于 GEO v1 正式模式
        # 2. 当前模型是否支持该模式
        to_geo_mode(mode)

        if mode not in supported_modes:
            raise ValueError(
                "腾讯元宝不支持该模型/模式组合："
                f"{model.value} + {mode.value}"
            )

    for question in questions:
        for mode in modes:
            tasks.append(
                YuanbaoTask(
                    question_id=question.question_id,
                    question=question.question,
                    model=model,
                    mode=mode,
                )
            )

    return tasks


class YuanbaoBatchRunner:

    def __init__(
            self,
            client: YuanbaoClient,
            batch_id: str,
            product: str,
    ):
        self.client = client
        self.config = client.config
        self.batch_id = batch_id
        self.product = product
        self.started_at = ""
        self.finished_at = ""

    def run_task(
            self,
            task: YuanbaoTask,
    ) -> YuanbaoCollectionResult:

        mode_code = to_geo_mode(
            task.mode
        )

        task_id = build_task_id(
            batch_id=self.batch_id,
            question_id=task.question_id,
            mode_code=mode_code,
        )

        task.task_id = task_id

        result = self.client.collect(
            question=task.question,
            model=task.model,
            mode=task.mode,
        )

        result.question_id = task.question_id
        result.task_id = task.task_id
        result.mode_code = mode_code
        result.batch_id = self.batch_id
        result.product = self.product
        result.platform = "yuanbao"

        return result

    def run(
            self,
            tasks: list[YuanbaoTask],
    ) -> list[YuanbaoCollectionResult]:

        results = []

        self.started_at = utc_now_iso()

        try:
            for index, task in enumerate(tasks):
                print(
                    "=" * 80
                )

                print(
                    f"[TASK {index + 1}/{len(tasks)}]"
                )

                print(
                    task.question
                )

                result = self.run_task(
                    task
                )

                results.append(
                    result
                )

                print(
                    f"STATUS: {result.status}"
                )

                if (
                        result.status == "failed"
                        and result.error
                ):
                    print(
                        f"ERROR: {result.error}"
                    )

                if index < len(tasks) - 1:
                    time.sleep(
                        random.uniform(
                            self.config.task_delay_min,
                            self.config.task_delay_max,
                        )
                    )

        finally:
            self.finished_at = utc_now_iso()

        return results
