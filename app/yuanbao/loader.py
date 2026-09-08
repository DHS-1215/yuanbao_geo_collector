import csv
from app.yuanbao.geo_contract import build_question_id

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
            csv_id = row["id"].strip()
            question = row["question"].strip()

            question_id = build_question_id(
                csv_id=csv_id,
                question=question,
            )

            tasks.append(
                YuanbaoTask(
                    question_id=question_id,
                    question=question,
                    model=YuanbaoModel.HY3,
                    mode=YuanbaoMode.EXPERT,
                )
            )

    return tasks
