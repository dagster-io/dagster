from functools import partial
from os import path
from typing import List

from dagster import DagsterInstance
from dagster import __version__ as dagster_version
from dagster.cli.workspace.cli_target import get_workspace_process_context_from_kwargs
from dagster.core.workspace import WorkspaceProcessContext
from dagster_graphql import __version__ as dagster_graphql_version
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import FileResponse, HTMLResponse, JSONResponse
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


def create_app(_process_context: WorkspaceProcessContext, app_path_prefix: str, debug: bool):
    base_dir = path.dirname(__file__)

    bound_index_endpoint = partial(index_endpoint, base_dir, app_path_prefix)

    return Starlette(
        debug=debug,
        routes=[
            Route("/dagit_info", dagit_info_endpoint),
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
        kwargs={},
    )
    return create_app(process_context, app_path_prefix="", debug=False)
