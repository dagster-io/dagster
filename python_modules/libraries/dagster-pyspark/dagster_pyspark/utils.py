import os
import re
import zipfile

import dagster._check as check

DEFAULT_EXCLUDE = [
    r".*pytest.*",
    r".*__pycache__.*",
    r".*pyc$",
    r".*\/venv\/.*",
    r".*\.egg-info$",
    r".*\/logs\/.*",
]


def build_pyspark_zip(zip_file, path, exclude=DEFAULT_EXCLUDE) -> None:
    """Archives the current path into a file named `zip_file`.

    Args:
        zip_file (str): The name of the zip file to create.
        path (str): The path to archive.
        exclude (Optional[List[str]]): A list of regular expression patterns to exclude paths from
            the archive. Regular expressions will be matched against the absolute filepath with
            `re.search`.
    """
    check.str_param(zip_file, "zip_file")
    check.str_param(path, "path")

    with zipfile.ZipFile(zip_file, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(path):
            for fname in files:
                abs_fname = os.path.join(root, fname)

                # Skip various artifacts
                if any([re.search(pattern, abs_fname) for pattern in exclude]):
                    continue

                zf.write(abs_fname, os.path.relpath(os.path.join(root, fname), path))
