import hashlib
from pathlib import Path


def calculate_sha256(file_path: str | Path) -> str:
    path = Path(file_path)

    sha256 = hashlib.sha256()

    with path.open("rb") as f:
        while chunk := f.read(8192):
            sha256.update(chunk)

    return sha256.hexdigest()


def generate_checksums(
        files: list[str | Path],
) -> dict[str, str]:
    result = {}

    for file in files:
        path = Path(file)

        result[path.name] = calculate_sha256(path)

    return result
