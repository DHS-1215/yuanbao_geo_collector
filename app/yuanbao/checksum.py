import hashlib
from pathlib import Path


def calculate_sha256(
        file_path: str | Path,
) -> str:
    path = Path(file_path)

    sha256 = hashlib.sha256()

    with path.open("rb") as f:
        while chunk := f.read(8192):
            sha256.update(chunk)

    return sha256.hexdigest()


def generate_checksums(
        files: list[str | Path],
) -> dict[str, dict[str, str]]:
    file_checksums: dict[str, str] = {}

    for file in files:
        path = Path(file)

        file_checksums[
            path.name
        ] = calculate_sha256(
            path
        )

    return {
        "files": file_checksums
    }
