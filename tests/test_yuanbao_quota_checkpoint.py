import json
from types import SimpleNamespace

import pytest

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
from app.yuanbao.types import (
    YuanbaoMode,
    YuanbaoModel,
)


class QuotaCheckpointClient:

    def __init__(
            self,
            *,
            quota_question: str | None = None,
    ):
        self.quota_question = quota_question

        self.calls: list[str] = []

        self.page = SimpleNamespace(
            url="https://yuanbao.tencent.com/"
        )

        self.config = SimpleNamespace(
            task_delay_min=0,
            task_delay_max=0,

            task_retry_max=0,
            task_retry_delay_min=0,
            task_retry_delay_max=0,

            risk_control_retry_max=0,
            risk_control_delay_min=0,
            risk_control_delay_max=0,
        )

    def collect(
            self,
            question,
            model,
            mode,
    ):
        self.calls.append(
            question
        )

        if (
                self.quota_question
                and question
                == self.quota_question
        ):
            return YuanbaoCollectionResult(
                question=question,
                answer=(
                    "今日使用次数已达上限"
                ),
                model=model.value,
                mode=mode.value,
                conversation_url=(
                    self.page.url
                ),
                status="failed",
                error="账号额度已耗尽",
                acquisition_status=(
                    "quota_exhausted"
                ),
                validation_status=(
                    "NOT_APPLICABLE"
                ),
                is_complete=False,
                source_collection_status=(
                    "failed"
                ),
                source_count_raw=0,
            )

        return YuanbaoCollectionResult(
            question=question,
            answer="测试成功回答",
            model=model.value,
            mode=mode.value,
            conversation_url=(
                self.page.url
            ),
            status="success",
            acquisition_status="success",
            validation_status=(
                "NOT_APPLICABLE"
            ),
            is_complete=True,
            source_collection_status=(
                "success"
            ),
            source_count_raw=0,
        )

    def is_ready_after_account_switch(
            self,
    ):
        return True


def build_tasks():
    return [
        YuanbaoTask(
            question_id="ybq_quota_cp_001",
            question="第一题",
            model=YuanbaoModel.HY3,
            mode=YuanbaoMode.EXPERT,
        ),
        YuanbaoTask(
            question_id="ybq_quota_cp_002",
            question="第二题",
            model=YuanbaoModel.HY3,
            mode=YuanbaoMode.EXPERT,
        ),
    ]


def test_quota_q_keeps_checkpoint_and_next_run_resumes(
        tmp_path,
        monkeypatch,
):
    batch_id = "batch_quota_checkpoint"

    # ==================================================
    # 第一轮：
    # TASK 1 成功
    # TASK 2 额度耗尽
    # 用户输入 Q
    # ==================================================

    first_store = (
        YuanbaoCheckpointStore(
            tmp_path,
            batch_id,
        )
    )

    first_client = (
        QuotaCheckpointClient(
            quota_question="第二题",
        )
    )

    first_runner = (
        YuanbaoBatchRunner(
            client=first_client,
            batch_id=batch_id,
            product="鸿茅药酒",
            checkpoint_store=(
                first_store
            ),
        )
    )

    monkeypatch.setattr(
        "builtins.input",
        lambda _: "Q",
    )

    with pytest.raises(
            SystemExit
    ) as exc_info:
        first_runner.run(
            build_tasks()
        )

    assert exc_info.value.code == 2

    # 第一题正常执行，
    # 第二题碰到额度后退出。
    assert first_client.calls == [
        "第一题",
        "第二题",
    ]

    # ==================================================
    # 检查 interrupted 状态
    # ==================================================

    meta = json.loads(
        first_store.meta_path.read_text(
            encoding="utf-8"
        )
    )

    assert meta["status"] == (
        "interrupted"
    )

    assert meta["success_count"] == 1

    # active_batch 必须继续存在，
    # 否则下一次无法自动 RESUME。
    assert (
            first_store.active_path.exists()
            is True
    )

    # TASK 1 成功结果必须已经保存。
    result_files = list(
        first_store.results_dir.glob(
            "*.json"
        )
    )

    assert len(result_files) == 1

    # ==================================================
    # 模拟下一次重新启动程序
    # ==================================================

    resolved_batch_id, resumed = (
        YuanbaoCheckpointStore
        .resolve_batch_id(
            tmp_path,
            new_batch_id=(
                "batch_new_should_not_be_used"
            ),
            force_new=False,
        )
    )

    assert resumed is True
    assert resolved_batch_id == batch_id

    # ==================================================
    # 第二轮：
    # 换号后额度恢复
    # ==================================================

    second_store = (
        YuanbaoCheckpointStore(
            tmp_path,
            resolved_batch_id,
        )
    )

    second_client = (
        QuotaCheckpointClient()
    )

    second_runner = (
        YuanbaoBatchRunner(
            client=second_client,
            batch_id=(
                resolved_batch_id
            ),
            product="鸿茅药酒",
            checkpoint_store=(
                second_store
            ),
        )
    )

    results = second_runner.run(
        build_tasks()
    )

    # 第一题必须走 checkpoint，
    # 不能再次请求腾讯元宝。
    assert second_client.calls == [
        "第二题",
    ]

    assert len(results) == 2

    assert all(
        result.status == "success"
        and result.is_complete
        for result in results
    )

    # ==================================================
    # 最终批次应正常完成
    # ==================================================

    final_meta = json.loads(
        second_store.meta_path.read_text(
            encoding="utf-8"
        )
    )

    assert final_meta["status"] == (
        "completed"
    )

    assert final_meta[
               "completed_count"
           ] == 2

    assert final_meta[
               "success_count"
           ] == 2

    assert final_meta[
               "failed_count"
           ] == 0

    # 全部完成后 active pointer
    # 应自动删除。
    assert (
            second_store.active_path.exists()
            is False
    )
