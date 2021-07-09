from dagster import __version__ as dagster_version
from dagster_graphql import __version__ as dagster_graphql_version
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route

from .version import __version__


async def dagit_info_endpoint(_request):
    return JSONResponse(
        {
            "dagit_version": __version__,
            "dagster_version": dagster_version,
            "dagster_graphql_version": dagster_graphql_version,
        }
    )


def create_app():
    return Starlette(routes=[Route("/dagit_info", dagit_info_endpoint)])
