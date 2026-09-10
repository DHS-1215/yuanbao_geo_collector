from types import SimpleNamespace

from app.yuanbao.checkpoint import (
    YuanbaoCheckpointStore,
)
from app.yuanbao.result import (
    YuanbaoCollectionResult,
)
from app.yuanbao.runner import (
    YuanbaoBatchRunner,
    YuanbaoTask,
)
from app.yuanbao.source import (
    YuanbaoSource,
)
from app.yuanbao.types import (
    YuanbaoMode,
    YuanbaoModel,
)


class FakeClient:

    def __init__(
            self,
            result_status="success",
    ):
        self.calls = 0

        self.result_status = (
            result_status
        )

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
        self.calls += 1

        if (
                self.result_status
                == "failed"
        ):
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

        return YuanbaoCollectionResult(
            question=question,
            answer="测试回答",
            model=model.value,
            mode=mode.value,
            conversation_url="test",
            sources=[
                YuanbaoSource(
                    index=1,
                    source="测试来源",
                    title="测试标题",
                    description="测试摘要",
                    url="https://example.com",
                    domain="example.com",
                )
            ],
            status="success",
            is_complete=True,
        )


def build_task():
    return YuanbaoTask(
        question_id="ybq_test_001",
        question="测试问题",
        model=YuanbaoModel.HY3,
        mode=YuanbaoMode.EXPERT,
    )


def test_checkpoint_round_trip(
        tmp_path,
):
    store = YuanbaoCheckpointStore(
        tmp_path,
        "batch_test",
    )

    store.initialize(
        product="鸿茅药酒",
        planned_count=1,
    )

    result = YuanbaoCollectionResult(
        question="测试问题",
        answer="测试回答",
        model="Hy3",
        mode="专家模式",
        conversation_url="test",
        task_id="task_001",
        question_id="question_001",
        mode_code="expert",
        batch_id="batch_test",
        product="鸿茅药酒",
        sources=[
            YuanbaoSource(
                index=1,
                source="测试来源",
                title="测试标题",
                description="测试摘要",
                url="https://example.com",
                domain="example.com",
            )
        ],
    )

    store.save_result(
        result
    )

    restored = store.load_result(
        "task_001"
    )

    assert restored is not None
    assert restored.answer == "测试回答"
    assert len(restored.sources) == 1

    assert (
            restored.sources[0].url
            == "https://example.com"
    )


def test_success_checkpoint_is_skipped(
        tmp_path,
):
    store = YuanbaoCheckpointStore(
        tmp_path,
        "batch_test",
    )

    first_client = FakeClient()

    first_runner = YuanbaoBatchRunner(
        client=first_client,
        batch_id="batch_test",
        product="鸿茅药酒",
        checkpoint_store=store,
    )

    first_runner.run(
        [build_task()]
    )

    assert first_client.calls == 1

    second_client = FakeClient()

    second_runner = YuanbaoBatchRunner(
        client=second_client,
        batch_id="batch_test",
        product="鸿茅药酒",
        checkpoint_store=store,
    )

    results = second_runner.run(
        [build_task()]
    )

    assert second_client.calls == 0
    assert len(results) == 1
    assert results[0].status == "success"


def test_failed_checkpoint_is_retried(
        tmp_path,
):
    store = YuanbaoCheckpointStore(
        tmp_path,
        "batch_test",
    )

    failed_client = FakeClient(
        result_status="failed"
    )

    failed_runner = YuanbaoBatchRunner(
        client=failed_client,
        batch_id="batch_test",
        product="鸿茅药酒",
        checkpoint_store=store,
    )

    failed_runner.run(
        [build_task()]
    )

    assert failed_client.calls == 1

    success_client = FakeClient()

    success_runner = YuanbaoBatchRunner(
        client=success_client,
        batch_id="batch_test",
        product="鸿茅药酒",
        checkpoint_store=store,
    )

    results = success_runner.run(
        [build_task()]
    )

    assert success_client.calls == 1
    assert results[0].status == "success"


def test_failed_batch_is_resumable(
        tmp_path,
):
    store = YuanbaoCheckpointStore(
        tmp_path,
        "batch_old",
    )

    failed_client = FakeClient(
        result_status="failed"
    )

    runner = YuanbaoBatchRunner(
        client=failed_client,
        batch_id="batch_old",
        product="鸿茅药酒",
        checkpoint_store=store,
    )

    runner.run(
        [build_task()]
    )

    batch_id, resumed = (
        YuanbaoCheckpointStore
        .resolve_batch_id(
            tmp_path,
            "batch_new",
        )
    )

    assert resumed is True

    assert (
            batch_id
            == "batch_old"
    )
