import json
import struct
import zlib
from pathlib import Path

import pytest

from app.yuanbao.exporter import (
    YuanbaoExporter,
)
from app.yuanbao.result import (
    YuanbaoCollectionResult,
)
from app.yuanbao.screenshot import (
    validate_yuanbao_screenshot,
)


def _png_chunk(
        chunk_type: bytes,
        data: bytes,
) -> bytes:
    crc = zlib.crc32(
        chunk_type
    )

    crc = zlib.crc32(
        data,
        crc,
    ) & 0xFFFFFFFF

    return (
        struct.pack(
            ">I",
            len(data),
        )
        + chunk_type
        + data
        + struct.pack(
            ">I",
            crc,
        )
    )


def _build_png(
        width: int = 4,
        height: int = 5,
) -> bytes:
    signature = (
        b"\x89PNG\r\n\x1a\n"
    )

    ihdr = struct.pack(
        ">IIBBBBB",
        width,
        height,
        8,
        6,
        0,
        0,
        0,
    )

    row = (
        b"\x00"
        + b"\x00\x00\x00\xff"
        * width
    )

    raw = row * height

    return (
        signature
        + _png_chunk(
            b"IHDR",
            ihdr,
        )
        + _png_chunk(
            b"IDAT",
            zlib.compress(
                raw
            ),
        )
        + _png_chunk(
            b"IEND",
            b"",
        )
    )


def _build_result(
        screenshot_path: Path,
) -> YuanbaoCollectionResult:
    evidence = (
        validate_yuanbao_screenshot(
            screenshot_path
        )
    )

    return YuanbaoCollectionResult(
        question="测试问题",
        answer="测试回答",
        model="Hy3",
        mode="专家模式",
        conversation_url=(
            "https://yuanbao.tencent.com/"
        ),
        task_id="yb_t_test_screenshot_001",
        question_id="ybq_test_001",
        mode_code="expert",
        batch_id="batch_export_screenshot",
        product="鸿茅药酒",
        platform="yuanbao",
        status="success",
        acquisition_status="success",
        validation_status="NOT_APPLICABLE",
        is_complete=True,
        source_collection_status="success",
        source_count_raw=0,
        screenshot_path=str(
            screenshot_path.resolve()
        ),
        screenshot_sha256=(
            evidence.sha256
        ),
        screenshot_size_bytes=(
            evidence.size_bytes
        ),
        screenshot_width=(
            evidence.width
        ),
        screenshot_height=(
            evidence.height
        ),
    )


def test_exporter_copies_screenshot_and_writes_reference(
        tmp_path,
):
    source = (
        tmp_path
        / "collector"
        / "source.png"
    )

    source.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    source.write_bytes(
        _build_png()
    )

    result = _build_result(
        source
    )

    output = (
        tmp_path
        / "package"
    )

    YuanbaoExporter().export(
        [result],
        str(output),
    )

    screenshot_ref = (
        "screenshots/"
        f"{result.task_id}.png"
    )

    copied = (
        output
        / screenshot_ref
    )

    assert copied.is_file()

    assert (
        copied.read_bytes()
        == source.read_bytes()
    )

    answers = [
        json.loads(line)
        for line in (
            output
            / "answers.jsonl"
        ).read_text(
            encoding="utf-8"
        ).splitlines()
        if line.strip()
    ]

    assert len(answers) == 1

    answer = answers[0]

    assert (
        answer["screenshot_path"]
        == screenshot_ref
    )

    platform_meta = (
        answer["platform_meta_json"]
    )

    assert (
        platform_meta[
            "screenshot_sha256"
        ]
        == result.screenshot_sha256
    )

    assert (
        platform_meta[
            "screenshot_size_bytes"
        ]
        == result.screenshot_size_bytes
    )

    assert (
        platform_meta[
            "screenshot_width"
        ]
        == 4
    )

    assert (
        platform_meta[
            "screenshot_height"
        ]
        == 5
    )

    manifest = json.loads(
        (
            output
            / "manifest.json"
        ).read_text(
            encoding="utf-8"
        )
    )

    assert (
        manifest[
            "capabilities"
        ][
            "supports_screenshot"
        ]
        is True
    )

    checksums = json.loads(
        (
            output
            / "checksums.json"
        ).read_text(
            encoding="utf-8"
        )
    )

    assert (
        screenshot_ref
        in checksums["files"]
    )

    assert (
        checksums["files"][
            screenshot_ref
        ]
        == result.screenshot_sha256
    )


def test_exporter_rejects_screenshot_metadata_mismatch(
        tmp_path,
):
    source = (
        tmp_path
        / "collector"
        / "source.png"
    )

    source.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    source.write_bytes(
        _build_png()
    )

    result = _build_result(
        source
    )

    result.screenshot_sha256 = (
        "0" * 64
    )

    output = (
        tmp_path
        / "package"
    )

    with pytest.raises(
            ValueError,
            match="screenshot_sha256 mismatch",
    ):
        YuanbaoExporter().export(
            [result],
            str(output),
        )
