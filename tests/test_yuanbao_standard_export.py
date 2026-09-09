import json

from app.yuanbao.exporter import YuanbaoExporter
from app.yuanbao.geo_contract import (
    YUANBAO_PLATFORM_CODE,
    build_answer_id,
    build_occurrence_id,
)
from app.yuanbao.result import YuanbaoCollectionResult
from app.yuanbao.source import YuanbaoSource
from app.yuanbao.checksum import calculate_sha256


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


def test_export_writes_sources_jsonl(
        tmp_path,
):
    result = build_result()

    result.sources = [
        YuanbaoSource(
            index=1,
            source="人民网",
            title="测试来源一",
            description="测试摘要一",
            url="https://example.com/a",
            domain="example.com",
        ),
        YuanbaoSource(
            index=2,
            source="腾讯医典",
            title="测试来源二",
            description="测试摘要二",
            url="https://example.com/b",
            domain="example.com",
        ),
    ]

    result.source_count_raw = 2

    YuanbaoExporter().export(
        [result],
        str(tmp_path),
    )

    rows = read_jsonl(
        tmp_path / "sources.jsonl"
    )

    assert len(rows) == 2

    answer_id = build_answer_id(
        batch_id=result.batch_id,
        task_id=result.task_id,
    )

    first = rows[0]

    assert first["answer_id"] == answer_id
    assert first["source_order"] == 1

    assert (
            first["source_url_raw"]
            == "https://example.com/a"
    )

    assert (
            first["source_title_raw"]
            == "测试来源一"
    )

    assert (
            first["source_site_name_raw"]
            == "人民网"
    )

    assert (
            first["source_snippet"]
            == "测试摘要一"
    )

    assert (
            first["is_duplicate_in_answer"]
            is False
    )

    expected_occurrence_id = (
        build_occurrence_id(
            batch_id=result.batch_id,
            answer_id=answer_id,
            source_order=1,
            source_url_raw=(
                "https://example.com/a"
            ),
        )
    )

    assert (
            first["occurrence_id"]
            == expected_occurrence_id
    )


def test_duplicate_raw_url_is_marked(
        tmp_path,
):
    result = build_result()

    result.sources = [
        YuanbaoSource(
            index=1,
            source="来源一",
            title="标题一",
            description="摘要一",
            url="https://example.com/a",
        ),
        YuanbaoSource(
            index=2,
            source="来源一",
            title="标题二",
            description="摘要二",
            url="https://example.com/a",
        ),
    ]

    YuanbaoExporter().export(
        [result],
        str(tmp_path),
    )

    rows = read_jsonl(
        tmp_path / "sources.jsonl"
    )

    assert len(rows) == 2

    assert (
            rows[0]["is_duplicate_in_answer"]
            is False
    )

    assert (
            rows[1]["is_duplicate_in_answer"]
            is True
    )

    assert (
            rows[0]["occurrence_id"]
            != rows[1]["occurrence_id"]
    )


def test_blank_source_url_is_not_exported(
        tmp_path,
):
    result = build_result()

    result.sources = [
        YuanbaoSource(
            index=1,
            source="无链接来源",
            title="标题一",
            description="摘要一",
            url="",
        ),
        YuanbaoSource(
            index=2,
            source="正常来源",
            title="标题二",
            description="摘要二",
            url="https://example.com/b",
        ),
    ]

    YuanbaoExporter().export(
        [result],
        str(tmp_path),
    )

    rows = read_jsonl(
        tmp_path / "sources.jsonl"
    )

    assert len(rows) == 1

    assert (
            rows[0]["source_order"]
            == 2
    )

    assert (
            rows[0]["source_url_raw"]
            == "https://example.com/b"
    )


def test_empty_sources_still_create_sources_jsonl(
        tmp_path,
):
    result = build_result()

    result.sources = []

    YuanbaoExporter().export(
        [result],
        str(tmp_path),
    )

    path = (
            tmp_path
            / "sources.jsonl"
    )

    assert path.exists()

    rows = read_jsonl(
        path
    )

    assert rows == []


def test_export_writes_standard_manifest(
        tmp_path,
):
    result = build_result()

    YuanbaoExporter().export(
        [result],
        str(tmp_path),
        started_at=(
            "2026-09-09T01:00:00+00:00"
        ),
        finished_at=(
            "2026-09-09T01:10:00+00:00"
        ),
    )

    with open(
            tmp_path / "manifest.json",
            "r",
            encoding="utf-8",
    ) as f:
        manifest = json.load(f)

    assert (
            manifest["schema_version"]
            == "geo_package_v1"
    )

    assert (
            manifest["geo_batch_version"]
            == "geo_batch_v1"
    )

    assert (
            manifest["platform_code"]
            == "yuanbao"
    )

    assert (
            manifest["platform_name"]
            == "腾讯元宝"
    )

    assert (
            manifest["product_id"]
            == "hongmao_yaojiu"
    )

    assert (
            manifest["product_name"]
            == "鸿茅药酒"
    )

    assert (
            manifest["batch_id"]
            == "batch_test_001"
    )

    assert (
            manifest["collector_version"]
            == "0.1.0"
    )

    assert manifest["status"] == "PASS"

    assert (
            manifest["started_at"]
            == "2026-09-09T01:00:00+00:00"
    )

    assert (
            manifest["finished_at"]
            == "2026-09-09T01:10:00+00:00"
    )

    capabilities = (
        manifest["capabilities"]
    )

    assert (
            capabilities["supports_sources"]
            is True
    )

    assert (
            capabilities[
                "supports_multiple_modes"
            ]
            is True
    )

    assert (
            capabilities[
                "supports_screenshot"
            ]
            is False
    )


def test_manifest_failed_task_has_warnings(
        tmp_path,
):
    success = build_result(
        task_id="yb_t_success",
    )

    failed = build_result(
        task_id="yb_t_failed",
    )

    failed.status = "failed"
    failed.acquisition_status = "failed"
    failed.is_complete = False
    failed.answer = ""
    failed.error = "测试失败"

    YuanbaoExporter().export(
        [success, failed],
        str(tmp_path),
    )

    with open(
            tmp_path / "manifest.json",
            "r",
            encoding="utf-8",
    ) as f:
        manifest = json.load(f)

    assert (
            manifest["status"]
            == "PASS_WITH_WARNINGS"
    )

    assert (
            manifest["task_count"]
            == 2
    )

    assert (
            manifest["success_tasks"]
            == 1
    )

    assert (
            manifest["failed_tasks"]
            == 1
    )


def test_export_writes_formal_checksums(
        tmp_path,
):
    result = build_result()

    YuanbaoExporter().export(
        [result],
        str(tmp_path),
    )

    with open(
            tmp_path / "checksums.json",
            "r",
            encoding="utf-8",
    ) as f:
        checksums = json.load(f)

    assert set(
        checksums.keys()
    ) == {
               "files"
           }

    files = checksums["files"]

    expected_files = {
        "manifest.json",
        "tasks.jsonl",
        "answers.jsonl",
        "sources.jsonl",
    }

    assert (
            set(files.keys())
            == expected_files
    )

    for filename in expected_files:
        assert (
                files[filename]
                == calculate_sha256(
            tmp_path / filename
        )
        )

    assert (
            "checksums.json"
            not in files
    )


def test_export_removes_legacy_json_files(
        tmp_path,
):
    (
            tmp_path
            / "answers.json"
    ).write_text(
        "legacy",
        encoding="utf-8",
    )

    (
            tmp_path
            / "sources.json"
    ).write_text(
        "legacy",
        encoding="utf-8",
    )

    result = build_result()

    YuanbaoExporter().export(
        [result],
        str(tmp_path),
    )

    assert not (
            tmp_path
            / "answers.json"
    ).exists()

    assert not (
            tmp_path
            / "sources.json"
    ).exists()

    expected_files = {
        "manifest.json",
        "tasks.jsonl",
        "answers.jsonl",
        "sources.jsonl",
        "checksums.json",
    }

    actual_files = {
        path.name
        for path in tmp_path.iterdir()
        if path.is_file()
    }

    assert (
            actual_files
            == expected_files
    )
