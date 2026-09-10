from datetime import datetime
from types import SimpleNamespace

from app.yuanbao.result import (
    YuanbaoCollectionResult,
)
from app.yuanbao.runner import (
    YuanbaoBatchRunner,
    YuanbaoTask,
)
from app.yuanbao.types import (
    YuanbaoMode,
    YuanbaoModel,
)


class FakeClient:

    def __init__(self):
        self.config = SimpleNamespace(
            task_delay_min=0,
            task_delay_max=0,
            task_retry_max=0,
            task_retry_delay_min=0,
            task_retry_delay_max=0,
        )

    def collect(
            self,
            question,
            model,
            mode,
    ):
        return YuanbaoCollectionResult(
            question=question,
            answer="测试回答",
            model=model.value,
            mode=mode.value,
            conversation_url=(
                "https://yuanbao.tencent.com/test"
            ),
        )


def test_runner_records_batch_time_range():
    runner = YuanbaoBatchRunner(
        client=FakeClient(),
        batch_id="batch_test_001",
        product="鸿茅药酒",
    )

    task = YuanbaoTask(
        question_id="ybq_test_001",
        question="测试问题",
        model=YuanbaoModel.HY3,
        mode=YuanbaoMode.EXPERT,
    )

    results = runner.run(
        [task]
    )

    assert len(results) == 1

    assert runner.started_at
    assert runner.finished_at

    started = datetime.fromisoformat(
        runner.started_at
    )

    finished = datetime.fromisoformat(
        runner.finished_at
    )

    assert finished >= started
