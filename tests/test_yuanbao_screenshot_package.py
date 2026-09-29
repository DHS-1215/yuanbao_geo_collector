from zipfile import ZipFile

from app.yuanbao.packager import (
    PACKAGE_FILES,
    create_package,
)


def test_package_includes_screenshots(
        tmp_path,
):
    source = (
        tmp_path
        / "package"
    )

    source.mkdir()

    for filename in PACKAGE_FILES:
        (
            source
            / filename
        ).write_text(
            "{}",
            encoding="utf-8",
        )

    screenshots = (
        source
        / "screenshots"
    )

    screenshots.mkdir()

    first = (
        screenshots
        / "yb_t_001.png"
    )

    second = (
        screenshots
        / "yb_t_002.png"
    )

    first.write_bytes(
        b"png-one"
    )

    second.write_bytes(
        b"png-two"
    )

    zip_path = (
        tmp_path
        / "result.zip"
    )

    create_package(
        source,
        zip_path,
    )

    with ZipFile(
            zip_path,
            "r",
    ) as zip_file:
        names = set(
            zip_file.namelist()
        )

        assert set(
            PACKAGE_FILES
        ).issubset(
            names
        )

        assert (
            "screenshots/yb_t_001.png"
            in names
        )

        assert (
            "screenshots/yb_t_002.png"
            in names
        )

        assert (
            zip_file.read(
                "screenshots/yb_t_001.png"
            )
            == b"png-one"
        )

        assert (
            zip_file.read(
                "screenshots/yb_t_002.png"
            )
            == b"png-two"
        )
