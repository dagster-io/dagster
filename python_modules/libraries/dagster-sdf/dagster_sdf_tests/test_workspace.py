import multiprocessing

import pytest
from dagster._core.test_utils import environ
from dagster._utils.test import copy_directory
from dagster_sdf.sdf_workspace import SdfWorkspace

from .sdf_workspaces import test_csv_123_path

def rm_tree(path):
    for child in path.iterdir():
        if child.is_file() or child.is_symlink():
            child.unlink()
        else:
            rm_tree(child)
    path.rmdir()


@pytest.fixture(scope="session")
def shared_workspace_dir():
    with copy_directory(test_csv_123_path) as project_dir:
        yield project_dir


@pytest.fixture(scope="function")
def workspace_dir(shared_workspace_dir):
    output_dir = SdfWorkspace(shared_workspace_dir).output_dir
    if output_dir.exists():
        if output_dir.is_file() or output_dir.is_symlink():
            output_dir.unlink()
        else:
            rm_tree(output_dir)
    yield shared_workspace_dir


def test_local_dev(workspace_dir) -> None:
    my_workspace = SdfWorkspace(workspace_dir)
    assert not my_workspace.output_dir.exists()
    with environ({"DAGSTER_IS_DEV_CLI": "1"}):
        my_workspace = SdfWorkspace(workspace_dir)
        assert my_workspace.output_dir.exists()


def test_opt_in_env_var(workspace_dir) -> None:
    my_workspace = SdfWorkspace(workspace_dir)
    assert not my_workspace.output_dir.exists()
    with environ({"DAGSTER_SDF_COMPILE_ON_LOAD": "1"}):
        my_workspace = SdfWorkspace(workspace_dir)
        assert my_workspace.output_dir.exists()


def _init(workspace_dir):
    my_workspace = SdfWorkspace(workspace_dir)
    assert my_workspace.output_dir.exists()
    return


def test_concurrent_processes(workspace_dir):
    my_workspace = SdfWorkspace(workspace_dir)
    assert not my_workspace.output_dir.exists()
    with environ({"DAGSTER_IS_DEV_CLI": "1"}):
        procs = [multiprocessing.Process(target=_init, args=(workspace_dir,)) for _ in range(4)]
        for proc in procs:
            proc.start()

        for proc in procs:
            proc.join(timeout=30)
            assert proc.exitcode == 0

        assert my_workspace.output_dir.exists()
