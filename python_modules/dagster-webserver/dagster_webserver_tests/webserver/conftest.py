import pytest
from dagster import DagsterInstance, __version__
from dagster._cli.workspace.cli_target import WorkspaceOpts, workspace_opts_to_load_target
from dagster._core.workspace.context import WorkspaceProcessContext
from dagster_webserver.webserver import DagsterWebserver
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.testclient import TestClient


@pytest.fixture(scope="session")
def instance():
    return DagsterInstance.local_temp()


class TestDagsterWebserver(DagsterWebserver):
    def test_req_ctx_endpoint(self, request: Request):
        with self.request_context(request) as ctx:
            # instantiate cached property with backref
            _ = ctx.instance_queryer
            return JSONResponse({"name": ctx.__class__.__name__})

    def build_routes(self):
        return [
            Route("/test_request_context", self.test_req_ctx_endpoint),
            *super().build_routes(),
        ]


@pytest.fixture(scope="session")
def test_client(instance):
    process_context = WorkspaceProcessContext(
        instance=instance,
        version=__version__,
        read_only=False,
        workspace_load_target=workspace_opts_to_load_target(
            WorkspaceOpts(empty_workspace=True),
        ),
    )

    app = TestDagsterWebserver(process_context).create_asgi_app(debug=True)
    return TestClient(app)
