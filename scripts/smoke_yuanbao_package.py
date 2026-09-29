import json
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
        actual = set(names)

        print()
        print("[FILES]")

        for name in names:
            print(f"- {name}")

        expected_core = set(
            PACKAGE_FILES
        )

        missing_core = (
            expected_core
            - actual
        )

        if missing_core:
            raise RuntimeError(
                "ZIP 缺少核心文件："
                f"{sorted(missing_core)}"
            )

        screenshot_files = {
            name
            for name in actual
            if (
                name.startswith(
                    "screenshots/"
                )
                and name.endswith(
                    ".png"
                )
            )
        }

        allowed = (
            expected_core
            | screenshot_files
        )

        unexpected = (
            actual
            - allowed
        )

        if unexpected:
            raise RuntimeError(
                "ZIP 包含未允许的文件："
                f"{sorted(unexpected)}"
            )

        manifest = json.loads(
            zip_file.read(
                "manifest.json"
            ).decode(
                "utf-8"
            )
        )

        answer_rows = []

        for line in (
                zip_file.read(
                    "answers.jsonl"
                )
                .decode(
                    "utf-8"
                )
                .splitlines()
        ):
            if not line.strip():
                continue

            answer_rows.append(
                json.loads(
                    line
                )
            )

        screenshot_refs = {
            row["screenshot_path"]
            for row in answer_rows
            if row.get(
                "screenshot_path"
            )
        }

        missing_refs = (
            screenshot_refs
            - actual
        )

        if missing_refs:
            raise RuntimeError(
                "answers.jsonl 引用了"
                "不存在的截图："
                f"{sorted(missing_refs)}"
            )

        supports_screenshot = (
            manifest
            .get(
                "capabilities",
                {},
            )
            .get(
                "supports_screenshot",
                False,
            )
        )

        has_screenshots = bool(
            screenshot_files
        )

        if (
                supports_screenshot
                != has_screenshots
        ):
            raise RuntimeError(
                "manifest 截图能力声明"
                "与 ZIP 实际截图不一致："
                f"supports_screenshot="
                f"{supports_screenshot}, "
                f"screenshot_count="
                f"{len(screenshot_files)}"
            )

        if (
                supports_screenshot
                and not screenshot_refs
        ):
            raise RuntimeError(
                "manifest 声明支持截图，"
                "但 answers.jsonl "
                "没有截图引用"
            )

        print()
        print(
            "[SCREENSHOTS]",
            len(
                screenshot_files
            ),
        )

        print(
            "[SCREENSHOT REFS]",
            len(
                screenshot_refs
            ),
        )

    print()
    print("=" * 80)
    print("PACKAGE STATUS: PASS")
    print("=" * 80)


if __name__ == "__main__":
    main()
