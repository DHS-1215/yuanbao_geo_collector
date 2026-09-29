import json

import pytest

from app.yuanbao.checkpoint import (
    YuanbaoCheckpointStore,
)
from app.yuanbao.config import YuanbaoConfig
from app.yuanbao.result import (
    YuanbaoCollectionResult,
)
from app.yuanbao.runner import (
    YuanbaoBatchRunner,
    YuanbaoQuestion,
    YuanbaoSessionRotate,
    build_geo_tasks,
)


class FakeClient:

    def __init__(
            self,
            questions_per_session: int,
    ):
        self.config = YuanbaoConfig(
            task_delay_min=0.0,
            task_delay_max=0.0,
            task_retry_max=0,
            task_retry_delay_min=0.0,
            task_retry_delay_max=0.0,
            risk_control_retry_max=0,
            risk_control_delay_min=0.0,
            risk_control_delay_max=0.0,
            questions_per_session=(
                questions_per_session
            ),
        )

        self.calls = []

    def collect(
            self,
            question,
            model,
            mode,
    ):
        self.calls.append(
            (
                question,
                mode.value,
            )
        )

        return YuanbaoCollectionResult(
            question=question,
            answer="test answer",
            model=model.value,
            mode=mode.value,
            conversation_url=(
                "https://yuanbao.tencent.com/"
            ),
            status="success",
            acquisition_status="success",
            validation_status="NOT_APPLICABLE",
            is_complete=True,
            source_collection_status="success",
            source_count_raw=0,
        )


def build_tasks(
        question_count: int,
):
    questions = [
        YuanbaoQuestion(
            question_id=f"q{index:03d}",
            question=f"question {index}",
        )
        for index in range(
            1,
            question_count + 1,
        )
    ]

    return build_geo_tasks(
        questions
    )


def build_runner(
        *,
        client,
        store=None,
        batch_id="batch_session_test",
):
    return YuanbaoBatchRunner(
        client=client,
        batch_id=batch_id,
        product="test-product",
        checkpoint_store=store,
    )


def test_rotate_after_five_new_questions(
        tmp_path,
):
    store = YuanbaoCheckpointStore(
        tmp_path / "checkpoints",
        "batch_rotate",
    )

    client = FakeClient(
        questions_per_session=5,
    )

    runner = build_runner(
        client=client,
        store=store,
        batch_id="batch_rotate",
    )

    tasks = build_tasks(6)

    with pytest.raises(
        YuanbaoSessionRotate
    ):
        runner.run(
            tasks
        )

    # Five questions:
    # quick + expert = ten actual calls.
    assert len(client.calls) == 10

    saved_results = list(
        store.results_dir.glob(
            "*.json"
        )
    )

    # The tenth task must already be saved
    # before session rotation is raised.
    assert len(saved_results) == 10

    meta = json.loads(
        store.meta_path.read_text(
            encoding="utf-8",
        )
    )

    assert meta["status"] == "interrupted"


def test_checkpoint_skips_do_not_count(
        tmp_path,
):
    store = YuanbaoCheckpointStore(
        tmp_path / "checkpoints",
        "batch_resume",
    )

    # Seed five complete questions.
    # Rotation is disabled during seeding.
    seed_client = FakeClient(
        questions_per_session=0,
    )

    seed_runner = build_runner(
        client=seed_client,
        store=store,
        batch_id="batch_resume",
    )

    seed_runner.run(
        build_tasks(5)
    )

    assert len(seed_client.calls) == 10

    # Resume the same batch with six questions.
    # The old five questions must be skipped.
    resume_client = FakeClient(
        questions_per_session=5,
    )

    resume_runner = build_runner(
        client=resume_client,
        store=store,
        batch_id="batch_resume",
    )

    results = resume_runner.run(
        build_tasks(6)
    )

    # Only question 6 is actually collected.
    assert len(resume_client.calls) == 2

    # All old and new results still participate
    # in final batch completion.
    assert len(results) == 12

    # Only the newly collected question counts
    # toward this Chrome session.
    assert (
        resume_runner
        .session_questions_completed
        == 1
    )


def test_final_five_questions_do_not_rotate(
        tmp_path,
):
    store = YuanbaoCheckpointStore(
        tmp_path / "checkpoints",
        "batch_exact_five",
    )

    client = FakeClient(
        questions_per_session=5,
    )

    runner = build_runner(
        client=client,
        store=store,
        batch_id="batch_exact_five",
    )

    results = runner.run(
        build_tasks(5)
    )

    # Exactly five questions means ten calls.
    assert len(client.calls) == 10
    assert len(results) == 10

    # The batch is already finished, so no
    # unnecessary extra Chrome session.
    assert (
        runner.session_questions_completed
        == 5
    )

    meta = json.loads(
        store.meta_path.read_text(
            encoding="utf-8",
        )
    )

    assert meta["status"] == "completed"
