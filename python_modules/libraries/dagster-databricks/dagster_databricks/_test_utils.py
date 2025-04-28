import base64
import inspect
import os
import subprocess
import textwrap
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any, Callable, Optional

import dagster._check as check
import pytest
from databricks.sdk import WorkspaceClient
from databricks.sdk.service import files

from dagster_databricks.pipes import dbfs_tempdir

DAGSTER_PIPES_WHL_FILENAME = "dagster_pipes-1!0+dev-py3-none-any.whl"

# This has been manually uploaded to a test DBFS workspace.
DAGSTER_PIPES_WHL_PATH = f"dbfs:/FileStore/jars/{DAGSTER_PIPES_WHL_FILENAME}"


def get_repo_root() -> str:
    path = os.path.dirname(__file__)
    while not os.path.exists(os.path.join(path, ".git")):
        path = os.path.dirname(path)
    return path


# Upload the Dagster Pipes wheel to DBFS. Use this fixture to avoid needing to manually reupload
# dagster-pipes if it has changed between test runs.
@contextmanager
def upload_dagster_pipes_whl(databricks_client: WorkspaceClient) -> Iterator[str]:
    dbfs_client = files.DbfsAPI(databricks_client.api_client)
    repo_root = get_repo_root()
    orig_wd = os.getcwd()
    dagster_pipes_root = os.path.join(repo_root, "python_modules", "dagster-pipes")
    os.chdir(dagster_pipes_root)
    subprocess.check_call(["python", "setup.py", "bdist_wheel"])
    with dbfs_tempdir(dbfs_client) as tempdir:
        path = os.path.join(f"dbfs:{tempdir}", DAGSTER_PIPES_WHL_FILENAME)
        subprocess.check_call(
            # ["dbfs", "cp", "--overwrite", f"dist/{DAGSTER_PIPES_WHL_FILENAME}", DAGSTER_PIPES_WHL_PATH]
            ["dbfs", "cp", "--overwrite", f"dist/{DAGSTER_PIPES_WHL_FILENAME}", path]
        )
        os.chdir(orig_wd)
        yield path


@pytest.fixture
def databricks_client() -> WorkspaceClient:
    return WorkspaceClient(
        host=os.environ["DATABRICKS_HOST"],
        token=os.environ["DATABRICKS_TOKEN"],
    )


@contextmanager
def temp_dbfs_script(
    client: WorkspaceClient,
    *,
    script_fn: Optional[Callable[[], Any]] = None,
    script_file: Optional[str] = None,
    dbfs_path: Optional[str] = None,
) -> Iterator[str]:
    # drop the signature line
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
    dbfs_client = files.DbfsAPI(client.api_client)
    contents = base64.b64encode(source.encode("utf-8")).decode("utf-8")
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
