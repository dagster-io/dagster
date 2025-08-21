import hashlib
from collections.abc import Sequence
from pathlib import Path
from typing import Optional

from dagster_shared.scaffold import DEFAULT_FILE_EXCLUDE_PATTERNS

from dagster_dg_core.utils import hash_directory_metadata, hash_file_metadata


def hash_paths(
    paths: Sequence[Path],
    includes: Optional[Sequence[str]] = None,
    excludes: Sequence[str] = DEFAULT_FILE_EXCLUDE_PATTERNS,
    error_on_missing: bool = True,
) -> str:
    """Hash the given paths, including their metadata.

    Args:
        paths: The paths to hash.
        includes: A list of glob patterns to target, excluding files that don't match any of the patterns.
        excludes: A list of glob patterns to exclude, including files that match any of the patterns. Defaults to
            various Python-related files that are not relevant to the contents of the project.

    Returns:
        The hash of the paths.
    """
    hasher = hashlib.md5()
    for path in paths:
        if path.is_dir():
            hash_directory_metadata(
                hasher,
                path,
                includes=includes,
                excludes=excludes,
                error_on_missing=error_on_missing,
            )
        else:
            hash_file_metadata(hasher, path, error_on_missing=error_on_missing)
    return hasher.hexdigest()
