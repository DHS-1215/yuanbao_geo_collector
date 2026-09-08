from zipfile import ZipFile

from app.yuanbao.packager import (
    PACKAGE_FILES,
    create_package,
)


def main() -> None:
    print("=" * 80)
    print("YUANBAO PACKAGE TEST")
    print("=" * 80)

    zip_path = create_package(
        source_dir="output/test_batch",
        zip_path="output/yuanbao_geo_package.zip",
    )

    print(f"[ZIP] {zip_path}")

    with ZipFile(
            zip_path,
            "r",
    ) as zip_file:

        names = zip_file.namelist()

    print()
    print("[FILES]")

    for name in names:
        print(f"- {name}")

    expected = set(
        PACKAGE_FILES
    )

    actual = set(
        names
    )

    if actual != expected:
        raise RuntimeError(
            "ZIP 标准包文件不完整："
            f"expected={sorted(expected)}, "
            f"actual={sorted(actual)}"
        )

    print()
    print("=" * 80)
    print("PACKAGE STATUS: PASS")
    print("=" * 80)


if __name__ == "__main__":
    main()
