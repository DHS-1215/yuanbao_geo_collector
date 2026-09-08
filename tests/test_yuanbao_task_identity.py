from types import SimpleNamespace

from app.yuanbao.geo_contract import (
    build_question_id,
    build_task_id,
)
from app.yuanbao.loader import load_questions
from app.yuanbao.result import YuanbaoCollectionResult
from app.yuanbao.runner import (
    YuanbaoBatchRunner,
    YuanbaoTask,
)
from app.yuanbao.types import (
    YuanbaoMode,
    YuanbaoModel,
)


class FakeYuanbaoClient:
    def __init__(self):
        self.config = SimpleNamespace(
            task_delay_min=0,
            task_delay_max=0,
        )

    def collect(
            self,
            question: str,
            model: YuanbaoModel,
            mode: YuanbaoMode,
    ) -> YuanbaoCollectionResult:
        return YuanbaoCollectionResult(
            question=question,
            answer="测试回答",
            model=model.value,
            mode=mode.value,
            conversation_url="https://yuanbao.tencent.com/test",
        )


def test_loader_builds_question_id_from_csv():
    tasks = load_questions(
        "input/questions.csv"
    )

    task = tasks[0]

    expected_question_id = build_question_id(
        csv_id="001",
        question="鸿茅药酒是正规药品吗？",
    )

    assert task.question_id == expected_question_id
    assert task.task_id == ""
    assert task.mode == YuanbaoMode.EXPERT
    assert task.model == YuanbaoModel.HY3


def test_runner_generates_standard_task_id():
    question = "鸿茅药酒是正规药品吗？"

    question_id = build_question_id(
        csv_id="001",
        question=question,
    )

    task = YuanbaoTask(
        question_id=question_id,
        question=question,
        model=YuanbaoModel.HY3,
        mode=YuanbaoMode.EXPERT,
    )

    runner = YuanbaoBatchRunner(
        client=FakeYuanbaoClient(),
        batch_id="batch_test_001",
        product="鸿茅药酒",
    )

    result = runner.run_task(
        task
    )

    expected_task_id = build_task_id(
        batch_id="batch_test_001",
        question_id=question_id,
        mode_code="expert",
    )

    assert task.task_id == expected_task_id

    assert result.question_id == question_id
    assert result.task_id == expected_task_id
    assert result.mode_code == "expert"

    assert result.batch_id == "batch_test_001"
    assert result.product == "鸿茅药酒"
    assert result.platform == "yuanbao"


def test_same_question_quick_and_expert_get_different_task_ids():
    question = "鸿茅药酒是正规药品吗？"

    question_id = build_question_id(
        csv_id="001",
        question=question,
    )

    quick_task = YuanbaoTask(
        question_id=question_id,
        question=question,
        model=YuanbaoModel.HY3,
        mode=YuanbaoMode.QUICK,
    )

    expert_task = YuanbaoTask(
        question_id=question_id,
        question=question,
        model=YuanbaoModel.HY3,
        mode=YuanbaoMode.EXPERT,
    )

    runner = YuanbaoBatchRunner(
        client=FakeYuanbaoClient(),
        batch_id="batch_test_001",
        product="鸿茅药酒",
    )

    quick_result = runner.run_task(
        quick_task
    )

    expert_result = runner.run_task(
        expert_task
    )

    assert quick_result.question_id == expert_result.question_id

    assert quick_result.mode_code == "quick"
    assert expert_result.mode_code == "expert"

    assert quick_result.task_id != expert_result.task_id
