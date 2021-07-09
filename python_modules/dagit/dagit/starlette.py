from functools import partial
from os import path
from typing import Dict, List, Union

from dagit.templates.playground import TEMPLATE
from dagster import DagsterInstance
from dagster import __version__ as dagster_version
from dagster.cli.workspace.cli_target import get_workspace_process_context_from_kwargs
from dagster.core.workspace.context import WorkspaceProcessContext
from dagster_graphql import __version__ as dagster_graphql_version
from dagster_graphql.schema import create_schema
from graphene import Schema
from graphql.error import format_error as format_graphql_error
from starlette import status
from starlette.applications import Starlette
from starlette.concurrency import run_in_threadpool
from starlette.datastructures import QueryParams
from starlette.requests import Request
from starlette.responses import FileResponse, HTMLResponse, JSONResponse, PlainTextResponse
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles

from .version import __version__

ROOT_ADDRESS_STATIC_RESOURCES = [
    "/manifest.json",
    "/favicon.ico",
    "/favicon.png",
    "/asset-manifest.json",
    "/robots.txt",
    "/favicon_failed.ico",
    "/favicon_pending.ico",
    "/favicon_success.ico",
]


async def dagit_info_endpoint(_request):
    return JSONResponse(
        {
            "dagit_version": __version__,
            "dagster_version": dagster_version,
            "dagster_graphql_version": dagster_graphql_version,
        }
    )


async def graphql_http_endpoint(
    schema: Schema,
    process_context: WorkspaceProcessContext,
    app_path_prefix: str,
    request: Request,
):
    """
    fork of starlette GraphQLApp to allow for
        * our context type (crucial)
        * our GraphiQL playground (could change)
    """

    if request.method == "GET":
        # render graphiql
        if "text/html" in request.headers.get("Accept", ""):
            text = TEMPLATE.replace("{{ app_path_prefix }}", app_path_prefix)
            return HTMLResponse(text)

        data: Union[Dict[str, str], QueryParams] = request.query_params

    elif request.method == "POST":
        content_type = request.headers.get("Content-Type", "")

        if "application/json" in content_type:
            data = await request.json()
        elif "application/graphql" in content_type:
            body = await request.body()
            text = body.decode()
            data = {"query": text}
        elif "query" in request.query_params:
            data = request.query_params
        else:
            return PlainTextResponse(
                "Unsupported Media Type",
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            )

    else:
        return PlainTextResponse(
            "Method Not Allowed", status_code=status.HTTP_405_METHOD_NOT_ALLOWED
        )

    if "query" not in data:
        return PlainTextResponse(
            "No GraphQL query found in the request",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    query = data["query"]
    variables = data.get("variables")
    operation_name = data.get("operationName")

    # context manager? scoping?
    context = process_context.create_request_context()

    result = await run_in_threadpool(  # threadpool = aio event loop
        schema.execute,
        query,
        variables=variables,
        operation_name=operation_name,
        context=context,
    )

    error_data = [format_graphql_error(err) for err in result.errors] if result.errors else None
    response_data = {"data": result.data}
    if error_data:
        response_data["errors"] = error_data
    status_code = status.HTTP_400_BAD_REQUEST if result.errors else status.HTTP_200_OK

    return JSONResponse(response_data, status_code=status_code)


def index_endpoint(
    base_dir: str,
    app_path_prefix: str,
    _request: Request,
):
    """
    Serves root html
    """
    index_path = path.join(base_dir, "./webapp/build/index.html")

    try:
        with open(index_path) as f:
            rendered_template = f.read()
            return HTMLResponse(
                rendered_template.replace('href="/', f'href="{app_path_prefix}/')
                .replace('src="/', f'src="{app_path_prefix}/')
                .replace("__PATH_PREFIX__", app_path_prefix)
            )
    except FileNotFoundError:
        raise Exception(
            """Can't find webapp files. Probably webapp isn't built. If you are using
            dagit, then probably it's a corrupted installation or a bug. However, if you are
            developing dagit locally, your problem can be fixed as follows:

            cd ./python_modules/
            make rebuild_dagit"""
        )


def create_root_static_endpoints(base_dir: str) -> List[Route]:
    def _static_file(file_path):
        return Route(
            file_path,
            lambda _: FileResponse(path=path.join(base_dir, f"./webapp/build{file_path}")),
        )

    return [_static_file(f) for f in ROOT_ADDRESS_STATIC_RESOURCES]


def create_app(
    process_context: WorkspaceProcessContext,
    debug: bool,
    app_path_prefix: str,
):
    graphql_schema = create_schema()
    base_dir = path.dirname(__file__)

    bound_index_endpoint = partial(index_endpoint, base_dir, app_path_prefix)

    return Starlette(
        debug=debug,
        routes=[
            Route("/dagit_info", dagit_info_endpoint),
            Route(
                "/graphql",
                partial(graphql_http_endpoint, graphql_schema, process_context, app_path_prefix),
                name="graphql-http",
                methods=["GET", "POST"],
            ),
            # static resources addressed at /static/
            Mount(
                "/static",
                StaticFiles(directory=path.join(base_dir, "./webapp/build/static")),
                name="static",
            ),
            # static resources addressed at /vendor/
            Mount(
                "/vendor",
                StaticFiles(directory=path.join(base_dir, "./webapp/build/vendor")),
                name="vendor",
            ),
            # specific static resources addressed at /
            *create_root_static_endpoints(base_dir),
            Route("/{path:path}", bound_index_endpoint),
            Route("/", bound_index_endpoint),
        ],
    )


def default_app():
    instance = DagsterInstance.get()
    process_context = get_workspace_process_context_from_kwargs(
        instance=instance,
        version=__version__,
        read_only=False,
        kwargs={},
    )
    return create_app(process_context, app_path_prefix="", debug=False)
