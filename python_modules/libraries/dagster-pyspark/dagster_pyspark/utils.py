import os
import zipfile

import dagster._check as check


def build_pyspark_zip(zip_file, path):
    """Archives the current path into a file named `zip_file`"""
    check.str_param(zip_file, "zip_file")
    check.str_param(path, "path")

    with zipfile.ZipFile(zip_file, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(path):
            for fname in files:
                abs_fname = os.path.join(root, fname)

                # Skip various artifacts
                if "pytest" in abs_fname or "__pycache__" in abs_fname or "pyc" in abs_fname:
                    continue

                zf.write(abs_fname, os.path.relpath(os.path.join(root, fname), path))
