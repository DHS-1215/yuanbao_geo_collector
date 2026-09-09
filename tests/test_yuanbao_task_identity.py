import pytest
from types import SimpleNamespace

from app.yuanbao.geo_contract import (
    build_question_id,
    build_task_id,
)
from app.yuanbao.loader import load_questions
from app.yuanbao.result import YuanbaoCollectionResult
from app.yuanbao.runner import (
    YuanbaoBatchRunner,
    YuanbaoQuestion,
    YuanbaoTask,
    build_geo_tasks,
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
    questions = load_questions(
        "input/questions.csv"
    )

    question = questions[0]

    expected_question_id = build_question_id(
        csv_id="001",
        question="鸿茅药酒是正规药品吗？",
    )


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


def test_build_geo_tasks_expands_quick_and_expert():
    question = YuanbaoQuestion(
        question_id="ybq_test_001",
        question="测试问题",
    )

    tasks = build_geo_tasks(
        [question]
    )

    assert len(tasks) == 2

    assert tasks[0].question_id == "ybq_test_001"
    assert tasks[0].mode == YuanbaoMode.QUICK
    assert tasks[0].model == YuanbaoModel.HY3

    assert tasks[1].question_id == "ybq_test_001"
    assert tasks[1].mode == YuanbaoMode.EXPERT
    assert tasks[1].model == YuanbaoModel.HY3


def test_six_questions_expand_to_twelve_geo_tasks():
    questions = load_questions(
        "input/questions.csv"
    )

    tasks = build_geo_tasks(
        questions
    )

    assert len(questions) == 6
    assert len(tasks) == 12

    assert sum(
        task.mode == YuanbaoMode.QUICK
        for task in tasks
    ) == 6

    assert sum(
        task.mode == YuanbaoMode.EXPERT
        for task in tasks
    ) == 6


def test_thinking_cannot_enter_geo_task_batch():
    question = YuanbaoQuestion(
        question_id="ybq_test_001",
        question="测试问题",
    )

    with pytest.raises(
            ValueError,
            match="深度思考.*暂不纳入 GEO v1",
    ):
        build_geo_tasks(
            [question],
            modes=(
                YuanbaoMode.THINKING,
            ),
        )
