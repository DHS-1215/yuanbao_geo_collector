from types import SimpleNamespace

import pytest

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


class QuotaSequenceClient:

    def __init__(
            self,
            outcomes,
            readiness=None,
    ):
        self.outcomes = list(
            outcomes
        )

        self.readiness = list(
            readiness
            or [True]
        )

        self.calls = 0
        self.readiness_calls = 0

        self.page = SimpleNamespace(
            url="test"
        )

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

        if outcome == "quota":
            return YuanbaoCollectionResult(
                question=question,
                answer="今日使用次数已达上限",
                model=model.value,
                mode=mode.value,
                conversation_url="test",
                status="failed",
                error="账号额度已耗尽",
                acquisition_status=(
                    "quota_exhausted"
                ),
                is_complete=False,
            )

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

    def is_ready_after_account_switch(
            self,
    ):
        index = min(
            self.readiness_calls,
            len(self.readiness) - 1,
        )

        self.readiness_calls += 1

        return self.readiness[index]


def build_task():
    return YuanbaoTask(
        question_id="ybq_quota_001",
        question="测试账号切换",
        model=YuanbaoModel.HY3,
        mode=YuanbaoMode.EXPERT,
    )


def build_runner(
        client,
):
    return YuanbaoBatchRunner(
        client=client,
        batch_id="batch_quota_test",
        product="鸿茅药酒",
    )


def test_quota_switch_r_then_success(
        monkeypatch,
):
    client = QuotaSequenceClient(
        [
            "quota",
            "success",
        ]
    )

    monkeypatch.setattr(
        "builtins.input",
        lambda _: "R",
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
    assert client.readiness_calls == 1


def test_r_before_login_waits_for_next_r(
        monkeypatch,
):
    client = QuotaSequenceClient(
        [
            "quota",
            "success",
        ],
        readiness=[
            False,
            True,
        ],
    )

    answers = iter(
        [
            "R",
            "R",
        ]
    )

    monkeypatch.setattr(
        "builtins.input",
        lambda _: next(answers),
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

    # 未登录完成时不能再次请求元宝。
    assert client.calls == 2
    assert client.readiness_calls == 2


def test_quota_q_exits_and_keeps_batch_resumable(
        monkeypatch,
):
    client = QuotaSequenceClient(
        [
            "quota",
            "success",
        ]
    )

    monkeypatch.setattr(
        "builtins.input",
        lambda _: "Q",
    )

    runner = build_runner(
        client
    )

    with pytest.raises(
            SystemExit
    ) as exc_info:
        runner.run_task_with_retry(
            build_task()
        )

    assert exc_info.value.code == 2

    # Q 以后绝不能继续请求。
    assert client.calls == 1
