import os
import shutil

import pytest
from automation.git import git_repo_root
from automation.release.dagster_module import DagsterModule


@pytest.fixture(scope="session")
def dagster_modules():
    return (
        DagsterModule("dagster", is_library=False),
        DagsterModule("dagster-k8s", is_library=True),
    )


@pytest.fixture(scope="function")
def bad_core_module():
    try:
        mod = os.path.join(git_repo_root(), "python_modules", "bad_core_module")
        os.mkdir(mod)
        yield
    finally:
        shutil.rmtree(mod, ignore_errors=True)
