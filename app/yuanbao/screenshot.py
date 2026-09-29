from __future__ import annotations

import hashlib
import struct
import zlib
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


class ScreenshotPage(Protocol):

    def screenshot(
            self,
            *,
            path: str,
            full_page: bool,
    ) -> object:
        ...


@dataclass(frozen=True)
class YuanbaoScreenshotEvidence:
    path: Path
    sha256: str
    size_bytes: int
    width: int
    height: int


def _sha256(
        path: Path,
) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        while True:
            chunk = handle.read(
                1024 * 1024
            )

            if not chunk:
                break

            digest.update(
                chunk
            )

    return digest.hexdigest()


def _read_exact(
        handle,
        size: int,
        label: str,
) -> bytes:
    data = handle.read(
        size
    )

    if len(data) != size:
        raise ValueError(
            f"truncated PNG {label}"
        )

    return data


def _read_png_dimensions(
        path: Path,
) -> tuple[int, int]:
    with path.open("rb") as handle:
        signature = _read_exact(
            handle,
            len(PNG_SIGNATURE),
            "signature",
        )

        if signature != PNG_SIGNATURE:
            raise ValueError(
                "invalid PNG signature"
            )

        width: int | None = None
        height: int | None = None

        seen_ihdr = False
        seen_idat = False
        seen_iend = False

        while True:
            header = handle.read(
                8
            )

            if not header:
                break

            if len(header) != 8:
                raise ValueError(
                    "truncated PNG chunk header"
                )

            length, chunk_type = (
                struct.unpack(
                    ">I4s",
                    header,
                )
            )

            chunk_data = _read_exact(
                handle,
                length,
                "chunk data",
            )

            expected_crc = struct.unpack(
                ">I",
                _read_exact(
                    handle,
                    4,
                    "chunk CRC",
                ),
            )[0]

            actual_crc = zlib.crc32(
                chunk_type
            )

            actual_crc = zlib.crc32(
                chunk_data,
                actual_crc,
            ) & 0xFFFFFFFF

            if actual_crc != expected_crc:
                raise ValueError(
                    "PNG chunk CRC mismatch"
                )

            if not seen_ihdr:
                if (
                        chunk_type != b"IHDR"
                        or length != 13
                ):
                    raise ValueError(
                        "PNG first chunk must be IHDR"
                    )

                width, height = (
                    struct.unpack(
                        ">II",
                        chunk_data[:8],
                    )
                )

                if (
                        width <= 0
                        or height <= 0
                ):
                    raise ValueError(
                        "PNG dimensions must be positive"
                    )

                seen_ihdr = True

            if chunk_type == b"IDAT":
                seen_idat = True

            if chunk_type == b"IEND":
                if length != 0:
                    raise ValueError(
                        "invalid PNG IEND chunk"
                    )

                seen_iend = True
                break

        if not seen_ihdr:
            raise ValueError(
                "PNG IHDR chunk missing"
            )

        if not seen_idat:
            raise ValueError(
                "PNG IDAT chunk missing"
            )

        if not seen_iend:
            raise ValueError(
                "PNG IEND chunk missing"
            )

        if handle.read(1):
            raise ValueError(
                "unexpected data after PNG IEND"
            )

    assert width is not None
    assert height is not None

    return (
        width,
        height,
    )


def validate_yuanbao_screenshot(
        output_path: str | Path,
) -> YuanbaoScreenshotEvidence:
    path = Path(
        output_path
    )

    if not path.exists():
        raise ValueError(
            f"screenshot file missing: {path}"
        )

    if not path.is_file():
        raise ValueError(
            f"screenshot path is not a file: {path}"
        )

    size_bytes = (
        path.stat().st_size
    )

    if size_bytes <= 0:
        raise ValueError(
            f"screenshot file is empty: {path}"
        )

    width, height = (
        _read_png_dimensions(
            path
        )
    )

    return YuanbaoScreenshotEvidence(
        path=path,
        sha256=_sha256(
            path
        ),
        size_bytes=size_bytes,
        width=width,
        height=height,
    )


def capture_yuanbao_screenshot(
        page: ScreenshotPage,
        output_path: str | Path,
) -> YuanbaoScreenshotEvidence:
    path = Path(
        output_path
    )

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    page.screenshot(
        path=str(path),
        full_page=True,
    )

    return validate_yuanbao_screenshot(
        path
    )
