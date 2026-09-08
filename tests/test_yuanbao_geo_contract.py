import pytest

from app.yuanbao.geo_contract import (
    build_answer_id,
    build_occurrence_id,
    build_question_id,
    build_task_id,
    normalize_question_text,
    to_geo_mode,
)
from app.yuanbao.types import YuanbaoMode


def test_quick_mode_maps_to_geo_quick():
    assert to_geo_mode(YuanbaoMode.QUICK) == "quick"


def test_expert_mode_maps_to_geo_expert():
    assert to_geo_mode(YuanbaoMode.EXPERT) == "expert"


def test_thinking_mode_is_not_supported_by_geo_v1():
    with pytest.raises(
        ValueError,
        match="深度思考.*暂不纳入 GEO v1",
    ):
        to_geo_mode(YuanbaoMode.THINKING)


def test_normalize_question_text():
    assert (
        normalize_question_text("  第一行\r\n第二行\r  ")
        == "第一行\n第二行"
    )


def test_question_id_is_stable():
    first = build_question_id(
        "001",
        "鸿茅药酒是正规药品吗？",
    )
    second = build_question_id(
        "001",
        "鸿茅药酒是正规药品吗？",
    )

    assert first == second


def test_question_id_ignores_outer_whitespace():
    first = build_question_id(
        "001",
        "鸿茅药酒是正规药品吗？",
    )
    second = build_question_id(
        "001",
        "  鸿茅药酒是正规药品吗？  ",
    )

    assert first == second


def test_question_id_normalizes_line_endings():
    first = build_question_id(
        "001",
        "第一行\r\n第二行",
    )
    second = build_question_id(
        "001",
        "第一行\n第二行",
    )

    assert first == second


def test_question_id_changes_when_question_changes():
    first = build_question_id(
        "001",
        "鸿茅药酒是正规药品吗？",
    )
    second = build_question_id(
        "001",
        "鸿茅药酒有什么功效？",
    )

    assert first != second


def test_task_id_is_stable():
    question_id = build_question_id(
        "001",
        "鸿茅药酒是正规药品吗？",
    )

    first = build_task_id(
        "batch_001",
        question_id,
        "expert",
    )
    second = build_task_id(
        "batch_001",
        question_id,
        "expert",
    )

    assert first == second


def test_task_id_changes_with_mode():
    question_id = build_question_id(
        "001",
        "鸿茅药酒是正规药品吗？",
    )

    quick_id = build_task_id(
        "batch_001",
        question_id,
        "quick",
    )
    expert_id = build_task_id(
        "batch_001",
        question_id,
        "expert",
    )

    assert quick_id != expert_id


def test_task_id_changes_with_batch():
    question_id = build_question_id(
        "001",
        "鸿茅药酒是正规药品吗？",
    )

    first = build_task_id(
        "batch_001",
        question_id,
        "expert",
    )
    second = build_task_id(
        "batch_002",
        question_id,
        "expert",
    )

    assert first != second


def test_answer_id_is_stable():
    first = build_answer_id(
        "batch_001",
        "yb_t_example",
    )
    second = build_answer_id(
        "batch_001",
        "yb_t_example",
    )

    assert first == second


def test_occurrence_id_is_stable():
    first = build_occurrence_id(
        "batch_001",
        "yb_a_example",
        1,
        "https://example.com/page",
    )
    second = build_occurrence_id(
        "batch_001",
        "yb_a_example",
        1,
        "https://example.com/page",
    )

    assert first == second


def test_occurrence_id_changes_with_source_order():
    first = build_occurrence_id(
        "batch_001",
        "yb_a_example",
        1,
        "https://example.com/page",
    )
    second = build_occurrence_id(
        "batch_001",
        "yb_a_example",
        2,
        "https://example.com/page",
    )

    assert first != second


def test_occurrence_id_changes_with_url():
    first = build_occurrence_id(
        "batch_001",
        "yb_a_example",
        1,
        "https://example.com/a",
    )
    second = build_occurrence_id(
        "batch_001",
        "yb_a_example",
        1,
        "https://example.com/b",
    )

    assert first != second


def test_generated_ids_fit_database_limits():
    question_id = build_question_id(
        "001",
        "鸿茅药酒是正规药品吗？",
    )
    task_id = build_task_id(
        "batch_001",
        question_id,
        "expert",
    )
    answer_id = build_answer_id(
        "batch_001",
        task_id,
    )
    occurrence_id = build_occurrence_id(
        "batch_001",
        answer_id,
        1,
        "https://example.com/page",
    )

    assert len(question_id) <= 64
    assert len(task_id) <= 128
    assert len(answer_id) <= 128
    assert len(occurrence_id) <= 128