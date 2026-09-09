from zipfile import ZipFile

import pytest

from app.yuanbao.packager import (
    PACKAGE_FILES,
    create_package,
)

EXPECTED_PACKAGE_FILES = (
    "manifest.json",
    "tasks.jsonl",
    "answers.jsonl",
    "sources.jsonl",
    "checksums.json",
)


def prepare_package_files(
        directory,
):
    directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    for filename in EXPECTED_PACKAGE_FILES:
        (
                directory
                / filename
        ).write_text(
            "{}\n",
            encoding="utf-8",
        )


def test_package_files_match_geo_v1():
    assert (
            PACKAGE_FILES
            == EXPECTED_PACKAGE_FILES
    )


def test_create_package_contains_only_standard_files(
        tmp_path,
):
    source = (
            tmp_path
            / "package"
    )

    prepare_package_files(
        source
    )

    zip_path = create_package(
        source_dir=source,
        zip_path=(
                tmp_path
                / "yuanbao.zip"
        ),
    )

    with ZipFile(
            zip_path,
            "r",
    ) as zip_file:
        names = (
            zip_file.namelist()
        )

    assert (
            tuple(names)
            == EXPECTED_PACKAGE_FILES
    )


def test_create_package_rejects_missing_file(
        tmp_path,
):
    source = (
            tmp_path
            / "package"
    )

    prepare_package_files(
        source
    )

    (
            source
            / "sources.jsonl"
    ).unlink()

    with pytest.raises(
            FileNotFoundError,
            match="sources.jsonl",
    ):
        create_package(
            source_dir=source,
            zip_path=(
                    tmp_path
                    / "yuanbao.zip"
            ),
        )
