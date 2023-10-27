import pytest
from dagster import DagsterInstance, __version__
from dagster._cli.workspace.cli_target import get_workspace_process_context_from_kwargs
from dagster_webserver.webserver import DagsterWebserver
from starlette.testclient import TestClient


@pytest.fixture(scope="session")
def instance():
    return DagsterInstance.local_temp()


@pytest.fixture(scope="session")
def test_client(instance):
    process_context = get_workspace_process_context_from_kwargs(
        instance=instance,
        version=__version__,
        read_only=False,
        kwargs={"empty_workspace": True},
    )
    app = DagsterWebserver(process_context).create_asgi_app(debug=True)
    return TestClient(app)
