import json

from app.yuanbao.exporter import YuanbaoExporter
from app.yuanbao.geo_contract import (
    YUANBAO_PLATFORM_CODE,
    build_answer_id,
)
from app.yuanbao.result import YuanbaoCollectionResult


def read_jsonl(path):
    with open(
            path,
            "r",
            encoding="utf-8",
    ) as f:
        return [
            json.loads(line)
            for line in f
            if line.strip()
        ]


def build_result(
        *,
        task_id: str = "yb_t_test001",
        question_id: str = "ybq_001_test",
        mode_code: str = "expert",
) -> YuanbaoCollectionResult:
    return YuanbaoCollectionResult(
        question="鸿茅药酒是正规药品吗？",
        answer="测试回答",
        model="Hy3",
        mode="专家模式",
        conversation_url=(
            "https://yuanbao.tencent.com/test"
        ),
        status="success",
        task_id=task_id,
        question_id=question_id,
        mode_code=mode_code,
        batch_id="batch_test_001",
        product="鸿茅药酒",
        platform="yuanbao",
        acquisition_status="success",
        validation_status="NOT_APPLICABLE",
        is_complete=True,
        source_collection_status="success",
        source_count_raw=0,
        collected_at="2026-09-09T01:00:00+00:00",
    )


def test_export_writes_tasks_jsonl(tmp_path):
    result = build_result()

    YuanbaoExporter().export(
        [result],
        str(tmp_path),
    )

    rows = read_jsonl(
        tmp_path / "tasks.jsonl"
    )

    assert len(rows) == 1

    row = rows[0]

    assert row["task_id"] == result.task_id
    assert row["question_id"] == result.question_id
    assert row["question"] == result.question
    assert row["mode_code"] == "expert"

    assert (
            row["platform_code"]
            == YUANBAO_PLATFORM_CODE
    )

    assert row["batch_id"] == "batch_test_001"
    assert row["task_status"] == "success"


def test_export_writes_answers_jsonl(tmp_path):
    result = build_result()

    YuanbaoExporter().export(
        [result],
        str(tmp_path),
    )

    rows = read_jsonl(
        tmp_path / "answers.jsonl"
    )

    assert len(rows) == 1

    row = rows[0]

    expected_answer_id = build_answer_id(
        batch_id=result.batch_id,
        task_id=result.task_id,
    )

    assert row["answer_id"] == expected_answer_id
    assert row["task_id"] == result.task_id
    assert row["question_id"] == result.question_id
    assert row["mode_code"] == "expert"

    assert row["question_text"] == result.question
    assert row["answer_text_raw"] == "测试回答"
    assert row["answer_text_clean"] == "测试回答"

    assert row["acquisition_status"] == "success"
    assert row["validation_status"] == "NOT_APPLICABLE"
    assert row["is_complete"] is True

    assert row["source_collection_status"] == "success"
    assert row["source_count_raw"] == 0

    assert (
            row["platform_code"]
            == YUANBAO_PLATFORM_CODE
    )


def test_platform_specific_fields_go_into_meta(tmp_path):
    result = build_result()

    result.source_error = (
        "测试来源异常"
    )

    YuanbaoExporter().export(
        [result],
        str(tmp_path),
    )

    row = read_jsonl(
        tmp_path / "answers.jsonl"
    )[0]

    meta = row["platform_meta_json"]

    assert meta["model"] == "Hy3"
    assert meta["raw_mode"] == "专家模式"

    assert (
            meta["conversation_url"]
            == "https://yuanbao.tencent.com/test"
    )

    assert (
            meta["source_error"]
            == "测试来源异常"
    )


def test_quick_and_expert_have_different_answer_ids(
        tmp_path,
):
    quick = build_result(
        task_id="yb_t_quick",
        mode_code="quick",
    )

    quick.mode = "快速回答"

    expert = build_result(
        task_id="yb_t_expert",
        mode_code="expert",
    )

    YuanbaoExporter().export(
        [quick, expert],
        str(tmp_path),
    )

    rows = read_jsonl(
        tmp_path / "answers.jsonl"
    )

    assert len(rows) == 2

    assert (
            rows[0]["answer_id"]
            != rows[1]["answer_id"]
    )
