from __future__ import annotations

import shutil
import zipfile
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DIST_DIR = ROOT / "dist"

PACKAGE_DIR_NAME = "yuanbao_geo_collector"

INCLUDE_DIRS = (
    "app",
    "input",
    "scripts",
)

INCLUDE_FILES = (
    "requirements.txt",
    "README.md",
    "README_SERVER.txt",
    "setup_server.bat",
    "run_yuanbao_geo_all.bat",
)

IGNORE_NAMES = {
    "__pycache__",
    ".pytest_cache",
    ".git",
    ".venv",
    ".idea",
    ".chrome-profile",
    ".chrome-sessions",
}

IGNORE_SUFFIXES = {
    ".pyc",
    ".pyo",
    ".bak",
}


FORBIDDEN_ZIP_PARTS = {
    ".git",
    ".venv",
    ".idea",
    ".pytest_cache",
    "__pycache__",
    ".chrome-profile",
    ".chrome-sessions",
    ".env",
}


def ignore_filter(
    directory: str,
    names: list[str],
) -> set[str]:
    ignored: set[str] = set()

    for name in names:
        if name in IGNORE_NAMES:
            ignored.add(name)
            continue

        if any(
            name.endswith(suffix)
            for suffix in IGNORE_SUFFIXES
        ):
            ignored.add(name)

    return ignored


def main() -> None:
    DIST_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    staging_root = (
        DIST_DIR
        / "_server_package_build"
    )

    package_root = (
        staging_root
        / PACKAGE_DIR_NAME
    )

    if staging_root.exists():
        shutil.rmtree(
            staging_root
        )

    package_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    for name in INCLUDE_DIRS:
        source = ROOT / name

        if not source.exists():
            raise FileNotFoundError(
                f"Required directory missing: {source}"
            )

        shutil.copytree(
            source,
            package_root / name,
            ignore=ignore_filter,
        )

    for name in INCLUDE_FILES:
        source = ROOT / name

        if not source.exists():
            raise FileNotFoundError(
                f"Required file missing: {source}"
            )

        shutil.copy2(
            source,
            package_root / name,
        )

    # Server starts with a clean output directory.
    (
        package_root
        / "output"
    ).mkdir(
        exist_ok=True,
    )

    zip_base = (
        DIST_DIR
        / f"yuanbao_geo_collector_server_{timestamp}"
    )

    zip_path = Path(
        shutil.make_archive(
            str(zip_base),
            "zip",
            root_dir=staging_root,
        )
    )

    with zipfile.ZipFile(
        zip_path,
        "r",
    ) as archive:
        members = archive.namelist()

    forbidden_members = []

    for member in members:
        parts = set(
            Path(member).parts
        )

        if (
                parts
                & FORBIDDEN_ZIP_PARTS
        ):
            forbidden_members.append(
                member
            )

        if (
                member.endswith(".pyc")
                or member.endswith(".pyo")
        ):
            forbidden_members.append(
                member
            )

    if forbidden_members:
        raise RuntimeError(
            "Sensitive or forbidden files "
            "found in server package:\n"
            + "\n".join(
                sorted(
                    set(
                        forbidden_members
                    )
                )
            )
        )

    shutil.rmtree(
        staging_root
    )

    print(
        "[SERVER PACKAGE]",
        zip_path,
    )

    print(
        "[SIZE MB]",
        round(
            zip_path.stat().st_size
            / 1024
            / 1024,
            2,
        ),
    )


if __name__ == "__main__":
    main()
