import base64
import inspect
import os
import random
import string
import subprocess
import textwrap
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import dagster._check as check
import pytest
from dagster._utils import discover_oss_root
from databricks.sdk import WorkspaceClient
from databricks.sdk.service import files
from databricks.sdk.service.workspace import ImportFormat, Language

from dagster_databricks.pipes import dbfs_tempdir, volumes_tempdir

DAGSTER_PIPES_WHL_FILENAME = "dagster_pipes-1!0+dev-py3-none-any.whl"

# This has been manually uploaded to a test DBFS workspace.
DAGSTER_PIPES_WHL_PATH = f"dbfs:/FileStore/jars/{DAGSTER_PIPES_WHL_FILENAME}"


# Upload the Dagster Pipes wheel to DBFS. Use this fixture to avoid needing to manually reupload
# dagster-pipes if it has changed between test runs.
@contextmanager
def upload_dagster_pipes_whl(databricks_client: WorkspaceClient) -> Iterator[str]:
    dbfs_client = files.DbfsAPI(databricks_client.api_client)
    oss_root = discover_oss_root(Path(__file__))
    dagster_pipes_root = os.path.join(oss_root, "python_modules", "dagster-pipes")
    subprocess.check_call(["python", "-m", "build", "--wheel"], cwd=dagster_pipes_root)
    whl_path = os.path.join(dagster_pipes_root, "dist", DAGSTER_PIPES_WHL_FILENAME)
    with dbfs_tempdir(dbfs_client) as tempdir:
        dbfs_path = os.path.join(f"dbfs:{tempdir}", DAGSTER_PIPES_WHL_FILENAME)
        subprocess.check_call(["databricks", "fs", "cp", "--overwrite", whl_path, dbfs_path])
        yield dbfs_path


@contextmanager
def upload_dagster_pipes_whl_to_volume(
    databricks_client: WorkspaceClient, volume_path: str
) -> Iterator[str]:
    """Build the dagster-pipes wheel and upload it to a UC Volume. Yields the volume path
    suitable for ``pip install`` inside a Databricks notebook (``/Volumes/.../*.whl``).
    """
    files_client = files.FilesAPI(databricks_client.api_client)
    oss_root = discover_oss_root(Path(__file__))
    dagster_pipes_root = os.path.join(oss_root, "python_modules", "dagster-pipes")
    subprocess.check_call(["python", "-m", "build", "--wheel"], cwd=dagster_pipes_root)
    local_whl = os.path.join(dagster_pipes_root, "dist", DAGSTER_PIPES_WHL_FILENAME)
    with volumes_tempdir(files_client, volume_path) as tempdir:
        remote_path = f"{tempdir}/{DAGSTER_PIPES_WHL_FILENAME}"
        with open(local_whl, "rb") as f:
            files_client.upload(remote_path, f, overwrite=True)
        yield remote_path


@pytest.fixture
def databricks_client() -> WorkspaceClient:
    return WorkspaceClient(
        host=os.environ["DATABRICKS_HOST"],
        token=os.environ["DATABRICKS_TOKEN"],
    )


def get_databricks_notebook_path() -> str:
    return os.environ["DATABRICKS_NOTEBOOK_PATH"]


def get_databricks_python_file_path() -> str:
    return os.environ["DATABRICKS_PYTHON_FILE_PATH"]


def get_script_source(script_fn: Callable[[], Any] | None = None, script_file: str | None = None):
    if script_fn is None and script_file is None:
        raise ValueError("Must provide either script_fn or script_file")
    elif script_fn is not None and script_file is not None:
        raise ValueError("Must provide only one of script_fn or script_file")
    elif script_fn is not None:
        source = textwrap.dedent(inspect.getsource(script_fn).split("\n", 1)[1])
    elif script_file is not None:
        with open(script_file, "rb") as f:
            source = f.read().decode("utf-8")
    else:
        check.failed("Unreachable")
    return base64.b64encode(source.encode("utf-8")).decode("utf-8")


@contextmanager
def temp_dbfs_script(
    client: WorkspaceClient,
    *,
    script_fn: Callable[[], Any] | None = None,
    script_file: str | None = None,
    dbfs_path: str | None = None,
) -> Iterator[str]:
    contents = get_script_source(script_fn=script_fn, script_file=script_file)
    dbfs_client = files.DbfsAPI(client.api_client)
    if dbfs_path is None:
        with dbfs_tempdir(dbfs_client) as tempdir:
            script_path = os.path.join(tempdir, "script.py")
            dbfs_client.put(script_path, contents=contents, overwrite=True)
            yield script_path
    else:
        try:
            dbfs_client.put(dbfs_path, contents=contents, overwrite=True)
            yield dbfs_path
        finally:
            dbfs_client.delete(dbfs_path, recursive=False)


@contextmanager
def temp_workspace_notebook(
    client: WorkspaceClient,
    *,
    workspace_path: str,
    script_fn: Callable[[], Any] | None = None,
    script_file: str | None = None,
) -> Iterator[str]:
    contents = get_script_source(script_fn=script_fn, script_file=script_file)
    dirname = "".join(random.choices(string.ascii_letters, k=30))
    workspace_path = f"{workspace_path}/{dirname}"
    notebook_path = os.path.join(workspace_path, "temp-notebook")
    try:
        client.workspace.mkdirs(workspace_path)
        client.workspace.import_(
            path=notebook_path,
            content=contents,
            format=ImportFormat.SOURCE,
            language=Language.PYTHON,
            overwrite=True,
        )
        yield notebook_path
    finally:
        client.workspace.delete(workspace_path, recursive=True)
