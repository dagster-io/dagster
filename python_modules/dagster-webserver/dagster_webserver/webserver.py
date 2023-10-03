import gzip
import io
import uuid
from os import path, walk
from typing import Generic, List, TypeVar

import dagster._check as check
from dagster import __version__ as dagster_version
from dagster._annotations import deprecated
from dagster._core.debug import DebugRunPayload
from dagster._core.storage.cloud_storage_compute_log_manager import CloudStorageComputeLogManager
from dagster._core.storage.compute_log_manager import ComputeIOType
from dagster._core.storage.local_compute_log_manager import LocalComputeLogManager
from dagster._core.workspace.context import BaseWorkspaceRequestContext, IWorkspaceProcessContext
from dagster._seven import json
from dagster._utils import Counter, traced_counter
from dagster_graphql import __version__ as dagster_graphql_version
from dagster_graphql.schema import create_schema
from graphene import Schema
from starlette.datastructures import MutableHeaders
from starlette.exceptions import HTTPException
from starlette.middleware import Middleware
from starlette.requests import HTTPConnection, Request
from starlette.responses import (
    FileResponse,
    HTMLResponse,
    JSONResponse,
    PlainTextResponse,
    RedirectResponse,
    StreamingResponse,
)
from starlette.routing import Mount, Route, WebSocketRoute
from starlette.types import Message

from .graphql import GraphQLServer
from .version import __version__

T_IWorkspaceProcessContext = TypeVar("T_IWorkspaceProcessContext", bound=IWorkspaceProcessContext)


class DagsterWebserver(GraphQLServer, Generic[T_IWorkspaceProcessContext]):
    _process_context: T_IWorkspaceProcessContext
    _uses_app_path_prefix: bool

    def __init__(
        self,
        process_context: T_IWorkspaceProcessContext,
        app_path_prefix: str = "",
        uses_app_path_prefix: bool = True,
    ):
        self._process_context = process_context
        self._uses_app_path_prefix = uses_app_path_prefix
        super().__init__(app_path_prefix)

    def build_graphql_schema(self) -> Schema:
        return create_schema()

    def build_graphql_middleware(self) -> list:
        return []

    def relative_path(self, rel: str) -> str:
        return path.join(path.dirname(__file__), rel)

    def make_request_context(self, conn: HTTPConnection) -> BaseWorkspaceRequestContext:
        return self._process_context.create_request_context(conn)

    def build_middleware(self) -> List[Middleware]:
        return [Middleware(DagsterTracedCounterMiddleware)]

    def make_security_headers(self) -> dict:
        return {
            "Cache-Control": "no-store",
            "Feature-Policy": "microphone 'none'; camera 'none'",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "X-Content-Type-Options": "nosniff",
        }

    def make_csp_header(self, nonce: str) -> str:
        csp_conf_path = self.relative_path("webapp/build/csp-header.txt")
        try:
            with open(csp_conf_path, encoding="utf8") as f:
                csp_template = f.read()
                return csp_template.replace("NONCE-PLACEHOLDER", nonce)
        except FileNotFoundError:
            raise Exception("""
                CSP configuration file could not be found.
                If you are using dagster-webserver, then probably it's a corrupted installation or a bug.
                However, if you are developing dagster-webserver locally, your problem can be fixed by running
                "make rebuild_ui" in the project root.
                """)

    async def webserver_info_endpoint(self, _request: Request):
        return JSONResponse(
            {
                "dagster_webserver_version": __version__,
                "dagster_version": dagster_version,
                "dagster_graphql_version": dagster_graphql_version,
            }
        )

    async def download_debug_file_endpoint(self, request: Request):
        run_id = request.path_params["run_id"]
        context = self.make_request_context(request)

        run = context.instance.get_run_by_id(run_id)
        debug_payload = DebugRunPayload.build(context.instance, run)  # type: ignore  # (possible none)

        result = io.BytesIO()
        with gzip.GzipFile(fileobj=result, mode="wb") as file:
            debug_payload.write(file)

        result.seek(0)  # be kind, please rewind

        return StreamingResponse(result, media_type="application/gzip")

    async def download_notebook(self, request: Request):
        try:
            import nbformat  # nbconvert dependency
            from nbconvert import HTMLExporter
        except ImportError:
            return HTMLResponse(
                "Notebook support requires nbconvert, which is not installed. You can install "
                "nbconvert using dagster-webserver's 'notebook' extra via "
                "<code>pip install dagster-webserver[notebook]</code>"
            )

        context = self.make_request_context(request)
        code_location_name = request.query_params["repoLocName"]

        nb_path = request.query_params["path"]
        if not nb_path.endswith(".ipynb"):
            return PlainTextResponse("Invalid Path", status_code=400)

        # get ipynb content from grpc call
        notebook_content = context.get_external_notebook_data(code_location_name, nb_path)
        check.inst_param(notebook_content, "notebook_content", bytes)

        # parse content to HTML
        notebook = nbformat.reads(notebook_content, as_version=4)
        html_exporter = HTMLExporter()
        (body, resources) = html_exporter.from_notebook_node(notebook)
        return HTMLResponse("<style>" + resources["inlining"]["css"][0] + "</style>" + body)

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
            raise HTTPException(404, detail="No log files available for download")

        return FileResponse(
            context.instance.compute_log_manager.get_local_path(
                run_id,
                step_key,
                ComputeIOType(file_type),
            ),
            filename=f"{run_id}_{step_key}.{file_type}",
        )

    async def download_captured_logs_endpoint(self, request: Request):
        [*log_key, file_extension] = request.path_params["path"].split("/")
        context = self.make_request_context(request)
        compute_log_manager = context.instance.compute_log_manager

        if not isinstance(
            compute_log_manager, (LocalComputeLogManager, CloudStorageComputeLogManager)
        ):
            raise HTTPException(
                404, detail="Compute log manager is not compatible for local downloads"
            )

        if isinstance(compute_log_manager, CloudStorageComputeLogManager):
            io_type = ComputeIOType.STDOUT if file_extension == "out" else ComputeIOType.STDERR
            if compute_log_manager.cloud_storage_has_logs(
                log_key, io_type
            ) and not compute_log_manager.has_local_file(log_key, io_type):
                compute_log_manager.download_from_cloud_storage(log_key, io_type)
            location = compute_log_manager.local_manager.get_captured_local_path(
                log_key, file_extension
            )
        else:
            location = compute_log_manager.get_captured_local_path(log_key, file_extension)

        if not location or not path.exists(location):
            raise HTTPException(404, detail="No log files available for download")

        filebase = "__".join(log_key)
        return FileResponse(location, filename=f"{filebase}.{file_extension}")

    def index_html_endpoint(self, request: Request):
        """Serves root html."""
        index_path = self.relative_path("webapp/build/index.html")

        context = self.make_request_context(request)

        try:
            with open(index_path, encoding="utf8") as f:
                rendered_template = f.read()
                nonce = uuid.uuid4().hex
                headers = {
                    **{"Content-Security-Policy": self.make_csp_header(nonce)},
                    **self.make_security_headers(),
                }
                return HTMLResponse(
                    rendered_template.replace(
                        "BUILDTIME_ASSETPREFIX_REPLACE_ME", f"{self._app_path_prefix}"
                    )
                    .replace("__PATH_PREFIX__", self._app_path_prefix)
                    .replace(
                        '"__TELEMETRY_ENABLED__"', str(context.instance.telemetry_enabled).lower()
                    )
                    .replace("NONCE-PLACEHOLDER", nonce),
                    headers=headers,
                )
        except FileNotFoundError:
            raise Exception("""
                Can't find webapp files.
                If you are using dagster-webserver, then probably it's a corrupted installation or a bug.
                However, if you are developing dagster-webserver locally, your problem can be fixed by running
                "make rebuild_ui" in the project root.
                """)

    def build_static_routes(self):
        def _static_file(path, file_path):
            return Route(
                path,
                lambda _: FileResponse(path=file_path),
                name="root_static",
            )

        routes = []
        base_dir = self.relative_path("webapp/build/")
        for subdir, _, files in walk(base_dir):
            for file in files:
                full_path = path.join(subdir, file)
                # Replace path.sep to make sure our routes use forward slashes on windows
                mount_path = "/" + full_path[len(base_dir) :].replace(path.sep, "/")
                routes.append(_static_file(mount_path, full_path))

        # No build directory, this happens in a test environment. Don't fail loudly since we already have other tests that will fail loudly if
        # there is in fact no build
        if len(routes) == 0:
            # These are tested by an internal test without building the app.
            return [
                Route("/favicon.png", lambda _: FileResponse(path="/favicon")),
                Route(
                    "/vendor/graphql-playground/index.css",
                    lambda _: FileResponse(path="/vendor/graphql-playground/index.css"),
                ),
            ]

        return routes

    @deprecated(
        breaking_version="2.0",
        subject="/dagit_info and /dagit/notebook endpoint",
        emit_runtime_warning=False,
    )
    def build_routes(self):
        routes = (
            [
                Route("/server_info", self.webserver_info_endpoint),
                Route("/dagit_info", self.webserver_info_endpoint),
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
                    "/logs/{path:path}",
                    self.download_captured_logs_endpoint,
                ),
                Route(
                    "/notebook",
                    self.download_notebook,
                ),
                Route(
                    "/dagit/notebook",
                    self.download_notebook,
                ),
                Route(
                    "/download_debug/{run_id:str}",
                    self.download_debug_file_endpoint,
                ),
                Route("/{path:path}", self.index_html_endpoint),
                Route("/", self.index_html_endpoint),
            ]
        )

        if self._app_path_prefix:

            def _redirect(_):
                return RedirectResponse(url=self._app_path_prefix)

            return [
                Mount(self._app_path_prefix, routes=routes),
                Route("/", _redirect),
            ]
        else:
            return routes


class DagsterTracedCounterMiddleware:
    """Middleware for counting traced dagster calls.

    Args:
      app (ASGI application): ASGI application
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        traced_counter.set(Counter())

        def send_wrapper(message: Message):
            if message["type"] == "http.response.start":
                counter = traced_counter.get()
                if counter and isinstance(counter, Counter):
                    headers = MutableHeaders(scope=message)
                    headers.append("x-dagster-call-counts", json.dumps(counter.counts()))

            return send(message)

        await self.app(scope, receive, send_wrapper)
