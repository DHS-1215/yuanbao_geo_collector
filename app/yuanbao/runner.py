from __future__ import annotations

import random
import time
from dataclasses import dataclass

from app.yuanbao.client import YuanbaoClient
from app.yuanbao.result import YuanbaoCollectionResult
from app.yuanbao.types import (
    YuanbaoMode,
    YuanbaoModel,
)


@dataclass
class YuanbaoTask:
    question: str
    model: YuanbaoModel
    mode: YuanbaoMode


class YuanbaoBatchRunner:

    def __init__(
            self,
            client: YuanbaoClient,
    ):
        self.client = client
        self.config = client.config

    def run_task(
            self,
            task: YuanbaoTask,
    ) -> YuanbaoCollectionResult:
        return self.client.collect(
            question=task.question,
            model=task.model,
            mode=task.mode,
        )

    def run(
            self,
            tasks: list[YuanbaoTask],
    ) -> list[YuanbaoCollectionResult]:
        results = []

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

            if index < len(tasks) - 1:
                time.sleep(
                    random.uniform(
                        self.config.task_delay_min,
                        self.config.task_delay_max,
                    )
                )

        return results
