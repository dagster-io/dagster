import gzip
import io
import uuid
from os import path
from typing import List

from dagster import DagsterInstance
from dagster import __version__ as dagster_version
from dagster.cli.workspace.cli_target import get_workspace_process_context_from_kwargs
from dagster.core.debug import DebugRunPayload
from dagster.core.storage.compute_log_manager import ComputeIOType
from dagster.core.workspace.context import WorkspaceProcessContext, WorkspaceRequestContext
from dagster_graphql import __version__ as dagster_graphql_version
from dagster_graphql.schema import create_schema
from graphene import Schema
from starlette.exceptions import HTTPException
from starlette.middleware import Middleware
from starlette.requests import HTTPConnection, Request
from starlette.responses import FileResponse, HTMLResponse, JSONResponse, StreamingResponse
from starlette.routing import Mount, Route, WebSocketRoute
from starlette.staticfiles import StaticFiles

from .graphql import GraphQLServer
from .version import __version__

ROOT_ADDRESS_STATIC_RESOURCES = [
    "/manifest.json",
    "/favicon.ico",
    "/favicon.png",
    "/favicon.svg",
    "/favicon-run-pending.svg",
    "/favicon-run-failed.svg",
    "/favicon-run-success.svg",
    "/asset-manifest.json",
    "/robots.txt",
]


class DagitWebserver(GraphQLServer):
    def __init__(self, process_context: WorkspaceProcessContext, app_path_prefix: str = ""):
        self._process_context = process_context
        super().__init__(app_path_prefix)

    def build_graphql_schema(self) -> Schema:
        return create_schema()

    def build_graphql_middleware(self) -> list:
        return []

    def relative_path(self, rel: str) -> str:
        return path.join(path.dirname(__file__), rel)

    def make_request_context(self, conn: HTTPConnection) -> WorkspaceRequestContext:
        return self._process_context.create_request_context(conn)

    def build_middleware(self) -> List[Middleware]:
        return []

    async def dagit_info_endpoint(self, _request: Request):
        return JSONResponse(
            {
                "dagit_version": __version__,
                "dagster_version": dagster_version,
                "dagster_graphql_version": dagster_graphql_version,
            }
        )

    async def download_debug_file_endpoint(self, request: Request):
        run_id = request.path_params["run_id"]
        context = self.make_request_context(request)

        run = context.instance.get_run_by_id(run_id)
        debug_payload = DebugRunPayload.build(context.instance, run)

        result = io.BytesIO()
        with gzip.GzipFile(fileobj=result, mode="wb") as file:
            debug_payload.write(file)

        result.seek(0)  # be kind, please rewind

        return StreamingResponse(result, media_type="application/gzip")

    async def download_compute_logs_endpoint(self, request: Request):
        run_id = request.path_params["run_id"]
        step_key = request.path_params["step_key"]
        file_type = request.path_params["file_type"]
        context = self.make_request_context(request)

        file = context.instance.compute_log_manager.get_local_path(
            run_id,
            step_key,
            ComputeIOType(file_type),
        )

        if not path.exists(file):
            raise HTTPException(404)

        return FileResponse(
            context.instance.compute_log_manager.get_local_path(
                run_id,
                step_key,
                ComputeIOType(file_type),
            ),
            filename=f"{run_id}_{step_key}.{file_type}",
        )

    def index_html_endpoint(self, _request: Request):
        """
        Serves root html
        """
        index_path = self.relative_path("webapp/build/index.html")

        try:
            with open(index_path) as f:
                rendered_template = f.read()
                return HTMLResponse(
                    rendered_template.replace('href="/', f'href="{self._app_path_prefix}/')
                    .replace('src="/', f'src="{self._app_path_prefix}/')
                    .replace("__PATH_PREFIX__", self._app_path_prefix)
                    .replace("NONCE-PLACEHOLDER", uuid.uuid4().hex)
                )
        except FileNotFoundError:
            raise Exception(
                """
                Can't find webapp files.
                If you are using dagit, then probably it's a corrupted installation or a bug.
                However, if you are developing dagit locally, your problem can be fixed by running
                "make rebuild_dagit" in the project root.
                """
            )

    def root_static_file_routes(self) -> List[Route]:
        def _static_file(file_path):
            return Route(
                file_path,
                lambda _: FileResponse(path=self.relative_path(f"webapp/build{file_path}")),
                name="root_static",
            )

        return [_static_file(f) for f in ROOT_ADDRESS_STATIC_RESOURCES]

    def build_static_routes(self):
        return [
            # static resources addressed at /static/
            Mount(
                "/static",
                StaticFiles(
                    directory=self.relative_path("webapp/build/static"),
                    check_dir=False,
                ),
                name="static",
            ),
            # static resources addressed at /vendor/
            Mount(
                "/vendor",
                StaticFiles(
                    directory=self.relative_path("webapp/build/vendor"),
                    check_dir=False,
                ),
                name="vendor",
            ),
            # specific static resources addressed at /
            *self.root_static_file_routes(),
        ]

    def build_routes(self):
        return (
            [
                Route("/dagit_info", self.dagit_info_endpoint),
                Route(
                    "/graphql",
                    self.graphql_http_endpoint,
                    name="graphql-http",
                    methods=["GET", "POST"],
                ),
                WebSocketRoute(
                    "/graphql",
                    self.graphql_ws_endpoint,
                    name="graphql-ws",
                ),
            ]
            + self.build_static_routes()
            + [
                # download file endpoints
                Route(
                    "/download/{run_id:str}/{step_key:str}/{file_type:str}",
                    self.download_compute_logs_endpoint,
                ),
                Route(
                    "/download_debug/{run_id:str}",
                    self.download_debug_file_endpoint,
                ),
                Route("/{path:path}", self.index_html_endpoint),
                Route("/", self.index_html_endpoint),
            ]
        )


def default_app(debug=False):
    instance = DagsterInstance.get()
    process_context = get_workspace_process_context_from_kwargs(
        instance=instance,
        version=__version__,
        read_only=False,
        kwargs={},
    )

    return DagitWebserver(
        process_context,
    ).create_asgi_app(debug=debug)


def debug_app():
    return default_app(debug=True)
