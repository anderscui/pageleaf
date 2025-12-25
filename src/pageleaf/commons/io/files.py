# coding=utf-8
import json
from pathlib import Path
from typing import Callable, Optional, Iterator


def list_files(
        directory: str | Path,
        pattern: str = "*",
        excludes: Optional[Callable[[Path], bool]] = None
) -> Iterator[Path]:
    """
    Iterate a directory recursively, yield the absolute file paths.

    Args:
        directory: target dir.
        pattern: glob pattern for filenames (e.g. '*.pdf')
        excludes: function to exclude files

    Yields:
        Absolute Path objects.

    Example:
        # exclude all files under .git dir.
        list_files(".", excludes=lambda p: ".git" in p.parts)
    """
    directory = Path(directory).expanduser().resolve()
    if not directory.is_dir():
        raise ValueError(f"Directory not found: {directory}")

    if excludes is None:
        excludes = lambda _: False

    for file_path in directory.rglob(pattern):
        if file_path.is_file() and not excludes(file_path):
            yield file_path


def json_load(file):
    file = Path(file)
    with file.open('r', encoding='utf-8') as fin:
        return json.load(fin)


def json_dump(obj, file, ensure_ascii=False, indent=None):
    with open(file, 'w', encoding='utf-8') as fout:
        json.dump(obj, fout, ensure_ascii=ensure_ascii, indent=indent)
