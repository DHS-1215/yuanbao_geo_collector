import csv

from app.yuanbao.runner import YuanbaoTask
from app.yuanbao.types import (
    YuanbaoMode,
    YuanbaoModel,
)


def load_questions(
        path: str,
) -> list[YuanbaoTask]:
    tasks = []

    with open(
            path,
            "r",
            encoding="utf-8",
    ) as file:
        reader = csv.DictReader(
            file
        )

        for row in reader:
            tasks.append(
                YuanbaoTask(
                    question=row["question"],
                    model=YuanbaoModel.HY3,
                    mode=YuanbaoMode.EXPERT,
                )
            )

    return tasks
