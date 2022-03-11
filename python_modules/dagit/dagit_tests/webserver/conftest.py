import pytest
from dagit.webserver import DagitWebserver
from starlette.testclient import TestClient

from dagster import DagsterInstance, __version__
from dagster._cli.workspace.cli_target import get_workspace_process_context_from_kwargs


@pytest.fixture(scope="session")
def instance():
    return DagsterInstance.local_temp()


@pytest.fixture(scope="session")
# pylint: disable=redefined-outer-name
def test_client(instance):
    process_context = get_workspace_process_context_from_kwargs(
        instance=instance,
        version=__version__,
        read_only=False,
        kwargs={"empty_workspace": True},
    )
    app = DagitWebserver(process_context).create_asgi_app(debug=True)
    return TestClient(app)
