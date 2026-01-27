import os
import tempfile
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

import pytest


@pytest.fixture()
def temp_dir() -> Generator[str, Any, None]:
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@contextmanager
def create_template_file(tmpdir: str, filename: str, text: str) -> Generator[str, Any, None]:
    file_path = os.path.join(tmpdir, filename)
    with open(file_path, "w") as f:
        f.write(text)
    yield file_path


@pytest.fixture
def empty_config(monkeypatch):
    monkeypatch.setenv("DAGSTER_CLOUD_CLI_CONFIG", "/tmp/nosuchpath")
    monkeypatch.delenv("DAGSTER_CLOUD_ORGANIZATION", raising=False)
    monkeypatch.delenv("DAGSTER_CLOUD_API_TOKEN", raising=False)
    monkeypatch.delenv("DAGSTER_CLOUD_DEPLOYMENT", raising=False)
