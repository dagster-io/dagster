import pytest
from dagit.starlette import create_app
from dagster import DagsterInstance, __version__
from dagster.cli.workspace.cli_target import get_workspace_process_context_from_kwargs


@pytest.fixture(scope="session")
def instance():
    return DagsterInstance.local_temp()


@pytest.fixture(scope="session")
# pylint: disable=redefined-outer-name
def empty_app(instance):
    process_context = get_workspace_process_context_from_kwargs(
        instance=instance,
        version=__version__,
        read_only=False,
        kwargs={"empty_workspace": True},
    )
    return create_app(
        process_context,
        debug=True,
        app_path_prefix="",
    )
