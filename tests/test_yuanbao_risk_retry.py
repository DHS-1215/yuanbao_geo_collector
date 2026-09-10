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


class RiskSequenceClient:

    def __init__(
            self,
            outcomes,
    ):
        self.outcomes = list(
            outcomes
        )

        self.calls = 0
        self.recovery_calls = 0
        self.recovery_result = True

        self.config = SimpleNamespace(
            task_delay_min=0,
            task_delay_max=0,
            task_retry_max=2,
            task_retry_delay_min=0,
            task_retry_delay_max=0,
            risk_control_retry_max=1,
            risk_control_delay_min=0,
            risk_control_delay_max=0,
        )

    def recover_after_risk_control(
            self,
    ):
        self.recovery_calls += 1

        return self.recovery_result

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

        if outcome == "risk_control":
            return YuanbaoCollectionResult(
                question=question,
                answer="",
                model=model.value,
                mode=mode.value,
                conversation_url="test",
                status="failed",
                error="访问过于频繁",
                acquisition_status="risk_control",
                is_complete=False,
            )

        return YuanbaoCollectionResult(
            question=question,
            answer="",
            model=model.value,
            mode=mode.value,
            conversation_url="test",
            status="failed",
            error="普通测试失败",
            acquisition_status="failed",
            is_complete=False,
        )


def build_task():
    return YuanbaoTask(
        question_id="ybq_risk_001",
        question="测试风控恢复",
        model=YuanbaoModel.HY3,
        mode=YuanbaoMode.EXPERT,
    )


def build_runner(
        client,
):
    return YuanbaoBatchRunner(
        client=client,
        batch_id="batch_risk_test",
        product="鸿茅药酒",
    )


def test_risk_control_can_recover():
    client = RiskSequenceClient(
        [
            "risk_control",
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

    assert client.recovery_calls == 1
    assert result.status == "success"
    assert client.calls == 2


def test_repeated_risk_control_stops():
    client = RiskSequenceClient(
        [
            "risk_control",
            "risk_control",
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

    assert result.status == "failed"

    assert (
            result.acquisition_status
            == "risk_control"
    )

    assert client.calls == 2


def test_risk_control_does_not_use_fast_retry():
    client = RiskSequenceClient(
        [
            "risk_control",
            "risk_control",
        ]
    )

    client.config.task_retry_max = 5

    runner = build_runner(
        client
    )

    result = (
        runner.run_task_with_retry(
            build_task()
        )
    )

    assert (
            result.acquisition_status
            == "risk_control"
    )

    # 即使普通重试允许 5 次，
    # 风控也只允许 1 次恢复。
    assert client.calls == 2


def test_unrecovered_risk_stops_request():
    client = RiskSequenceClient(
        [
            "risk_control",
            "success",
        ]
    )

    client.recovery_result = False

    runner = build_runner(
        client
    )

    result = (
        runner.run_task_with_retry(
            build_task()
        )
    )

    assert result.status == "failed"

    assert (
            result.acquisition_status
            == "risk_control"
    )

    # 第一次发生风控后，
    # recovery 判定页面仍未恢复，
    # 因此绝不能进行第二次 collect。
    assert client.calls == 1

    assert client.recovery_calls == 1
