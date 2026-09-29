import struct
import zlib
from pathlib import Path

from app.yuanbao.checkpoint import (
    YuanbaoCheckpointStore,
)
from app.yuanbao.config import YuanbaoConfig
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


def _build_test_png(
        width: int = 2,
        height: int = 3,
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


class FakePage:

    def __init__(
            self,
            *,
            fail: bool = False,
    ):
        self.fail = fail
        self.calls = []

    def screenshot(
            self,
            *,
            path: str,
            full_page: bool,
    ):
        self.calls.append(
            (
                path,
                full_page,
            )
        )

        if self.fail:
            raise RuntimeError(
                "fake screenshot failure"
            )

        Path(path).write_bytes(
            _build_test_png()
        )


class FakeClient:

    def __init__(
            self,
            *,
            screenshot_fail: bool = False,
    ):
        self.page = FakePage(
            fail=screenshot_fail
        )

        self.config = YuanbaoConfig(
            task_delay_min=0.0,
            task_delay_max=0.0,
            task_retry_max=0,
            task_retry_delay_min=0.0,
            task_retry_delay_max=0.0,
            risk_control_retry_max=0,
            risk_control_delay_min=0.0,
            risk_control_delay_max=0.0,
            questions_per_session=5,
        )

    def collect(
            self,
            question,
            model,
            mode,
    ):
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


def _build_task():
    return YuanbaoTask(
        question_id="q001",
        question="test question",
        model=YuanbaoModel.HY3,
        mode=YuanbaoMode.EXPERT,
    )


def test_success_result_saves_screenshot_and_checkpoint(
        tmp_path,
        monkeypatch,
):
    monkeypatch.chdir(
        tmp_path
    )

    batch_id = (
        "batch_screenshot_success"
    )

    store = YuanbaoCheckpointStore(
        tmp_path / "checkpoints",
        batch_id,
    )

    client = FakeClient()

    runner = YuanbaoBatchRunner(
        client=client,
        batch_id=batch_id,
        product="test-product",
        checkpoint_store=store,
    )

    task = _build_task()

    results = runner.run(
        [task]
    )

    assert len(results) == 1

    result = results[0]

    assert result.status == "success"
    assert result.is_complete is True

    screenshot_path = Path(
        result.screenshot_path
    )

    expected_path = (
        tmp_path
        / "output"
        / "screenshots"
        / batch_id
        / f"{task.task_id}.png"
    ).resolve()

    assert screenshot_path == (
        expected_path
    )

    assert screenshot_path.is_file()

    assert result.screenshot_sha256
    assert len(
        result.screenshot_sha256
    ) == 64

    assert (
        result.screenshot_size_bytes
        == screenshot_path.stat().st_size
    )

    assert result.screenshot_width == 2
    assert result.screenshot_height == 3

    assert client.page.calls == [
        (
            str(
                expected_path
            ),
            True,
        )
    ]

    cached = store.load_result(
        task.task_id
    )

    assert cached is not None

    assert (
        cached.screenshot_path
        == result.screenshot_path
    )

    assert (
        cached.screenshot_sha256
        == result.screenshot_sha256
    )

    assert (
        cached.screenshot_size_bytes
        == result.screenshot_size_bytes
    )

    assert (
        cached.screenshot_width
        == 2
    )

    assert (
        cached.screenshot_height
        == 3
    )


def test_screenshot_failure_marks_task_failed(
        tmp_path,
        monkeypatch,
):
    monkeypatch.chdir(
        tmp_path
    )

    batch_id = (
        "batch_screenshot_failure"
    )

    store = YuanbaoCheckpointStore(
        tmp_path / "checkpoints",
        batch_id,
    )

    client = FakeClient(
        screenshot_fail=True
    )

    runner = YuanbaoBatchRunner(
        client=client,
        batch_id=batch_id,
        product="test-product",
        checkpoint_store=store,
    )

    task = _build_task()

    results = runner.run(
        [task]
    )

    assert len(results) == 1

    result = results[0]

    assert result.status == "failed"

    assert result.is_complete is False

    assert (
        result.validation_status
        == "SCREENSHOT_FAILED"
    )

    assert (
        "Screenshot capture failed:"
        in result.error
    )

    assert (
        "fake screenshot failure"
        in result.error
    )

    assert result.screenshot_path == ""
    assert result.screenshot_sha256 == ""

    assert (
        result.screenshot_size_bytes
        == 0
    )

    assert result.screenshot_width == 0
    assert result.screenshot_height == 0

    # Failed screenshot must not consume
    # the five-question session quota.
    assert (
        runner.session_questions_completed
        == 0
    )

    cached = store.load_result(
        task.task_id
    )

    assert cached is not None
    assert cached.status == "failed"
    assert cached.is_complete is False
