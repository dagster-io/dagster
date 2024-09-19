import os
import zipfile
from pathlib import Path

from dagster_pyspark.utils import build_pyspark_zip


def test_build_pyspark_zip(tmp_path):
    zip_path = tmp_path / "test.zip"
    root = Path(tmp_path / "root")
    os.mkdir(root)
    os.mkdir(root / "foo")
    os.mkdir(root / "foo/bar")
    with open(root / "foo/bar/baz.txt", "w") as f:
        f.write("hello world")
    with open(root / "foo/baz.txt", "w") as f:
        f.write("hello world")
    build_pyspark_zip(str(zip_path), str(root), exclude=[r".*/bar/.*"])
    with zipfile.ZipFile(zip_path, "r") as zf:
        assert zf.namelist() == ["foo/baz.txt"]
