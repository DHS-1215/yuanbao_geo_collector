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


class SequenceClient:

    def __init__(
            self,
            outcomes,
    ):
        self.outcomes = list(
            outcomes
        )

        self.calls = 0

        self.config = SimpleNamespace(
            task_delay_min=0,
            task_delay_max=0,
            task_retry_max=2,
            task_retry_delay_min=0,
            task_retry_delay_max=0,
        )

    def collect(
            self,
            question,
            model,
            mode,
    ):
        outcome = self.outcomes[
            min(
                self.calls,
                len(self.outcomes) - 1,
            )
        ]

        self.calls += 1

        if isinstance(
                outcome,
                Exception,
        ):
            raise outcome

        if outcome == "success":
            return YuanbaoCollectionResult(
                question=question,
                answer="测试回答",
                model=model.value,
                mode=mode.value,
                conversation_url="test",
                status="success",
                acquisition_status="success",
                is_complete=True,
            )

        return YuanbaoCollectionResult(
            question=question,
            answer="",
            model=model.value,
            mode=mode.value,
            conversation_url="test",
            status="failed",
            error="测试失败",
            acquisition_status="failed",
            is_complete=False,
        )


def build_task():
    return YuanbaoTask(
        question_id="ybq_retry_001",
        question="测试重试",
        model=YuanbaoModel.HY3,
        mode=YuanbaoMode.EXPERT,
    )


def build_runner(
        client,
):
    return YuanbaoBatchRunner(
        client=client,
        batch_id="batch_retry_test",
        product="鸿茅药酒",
    )


def test_retry_then_success():
    client = SequenceClient(
        [
            "failed",
            "success",
        ]
    )

    runner = build_runner(
        client
    )

    result = (
        runner.run_task_with_retry(
            build_task()
        )
    )

    assert result.status == "success"
    assert result.is_complete is True
    assert client.calls == 2


def test_retry_until_exhausted():
    client = SequenceClient(
        [
            "failed",
            "failed",
            "failed",
        ]
    )

    runner = build_runner(
        client
    )

    result = (
        runner.run_task_with_retry(
            build_task()
        )
    )

    assert result.status == "failed"
    assert result.is_complete is False
    assert client.calls == 3


def test_runner_exception_can_retry():
    client = SequenceClient(
        [
            RuntimeError(
                "模拟页面瞬时异常"
            ),
            "success",
        ]
    )

    runner = build_runner(
        client
    )

    result = (
        runner.run_task_with_retry(
            build_task()
        )
    )

    assert result.status == "success"
    assert client.calls == 2
