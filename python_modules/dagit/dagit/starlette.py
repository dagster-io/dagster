import gzip
import io
from asyncio import Queue, get_event_loop
from enum import Enum
from functools import partial
from os import path
from typing import Any, AsyncGenerator, Dict, List, Union

from dagit.templates.playground import TEMPLATE
from dagster import DagsterInstance
from dagster import __version__ as dagster_version
from dagster import check
from dagster.cli.workspace.cli_target import get_workspace_process_context_from_kwargs
from dagster.core.debug import DebugRunPayload
from dagster.core.workspace.context import WorkspaceProcessContext
from dagster_graphql import __version__ as dagster_graphql_version
from dagster_graphql.schema import create_schema
from graphene import Schema
from graphql.error import GraphQLError
from graphql.error import format_error as format_graphql_error
from graphql.execution import ExecutionResult
from rx import Observable
from starlette import status
from starlette.applications import Starlette
from starlette.concurrency import run_in_threadpool
from starlette.datastructures import QueryParams
from starlette.requests import Request
from starlette.responses import (
    FileResponse,
    HTMLResponse,
    JSONResponse,
    PlainTextResponse,
    StreamingResponse,
)
from starlette.routing import Mount, Route, WebSocketRoute
from starlette.staticfiles import StaticFiles
from starlette.types import Receive, Scope, Send
from starlette.websockets import WebSocket, WebSocketDisconnect, WebSocketState

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


class GraphQLWS(str, Enum):
    PROTOCOL = "graphql-ws"

    # https://github.com/apollographql/subscriptions-transport-ws/blob/master/PROTOCOL.md
    CONNECTION_INIT = "connection_init"
    CONNECTION_ACK = "connection_ack"
    CONNECTION_ERROR = "connection_error"
    CONNECTION_TERMINATE = "connection_terminate"
    CONNECTION_KEEP_ALIVE = "ka"
    START = "start"
    DATA = "data"
    ERROR = "error"
    COMPLETE = "complete"
    STOP = "stop"


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
    context = process_context.create_request_context(request)

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


async def graphql_ws_endpoint(
    schema: Schema,
    process_context: WorkspaceProcessContext,
    scope: Scope,
    receive: Receive,
    send: Send,
):
    """
    Implementation of websocket ASGI endpoint for GraphQL.
    Once we are free of conflicting deps, we should be able to use an impl from
    strawberry-graphql or the like.
    """

    websocket = WebSocket(scope=scope, receive=receive, send=send)

    observables = {}
    tasks = {}

    await websocket.accept(subprotocol=GraphQLWS.PROTOCOL)

    try:
        while (
            websocket.client_state != WebSocketState.DISCONNECTED
            and websocket.application_state != WebSocketState.DISCONNECTED
        ):
            message = await websocket.receive_json()
            operation_id = message.get("id")
            message_type = message.get("type")

            if message_type == GraphQLWS.CONNECTION_INIT:
                await websocket.send_json({"type": GraphQLWS.CONNECTION_ACK})

            elif message_type == GraphQLWS.CONNECTION_TERMINATE:
                await websocket.close()
            elif message_type == GraphQLWS.START:
                try:
                    data = message["payload"]
                    query = data["query"]
                    variables = data.get("variables")
                    operation_name = data.get("operation_name")

                    # correct scoping?
                    request_context = process_context.create_request_context(websocket)
                    async_result = schema.execute(
                        query,
                        variables=variables,
                        operation_name=operation_name,
                        context=request_context,
                        allow_subscriptions=True,
                    )
                except GraphQLError as error:
                    payload = format_graphql_error(error)
                    await _send_message(websocket, GraphQLWS.ERROR, payload, operation_id)
                    continue

                if isinstance(async_result, ExecutionResult):
                    if not async_result.errors:
                        check.failed(f"Only expect non-async result on error, got {async_result}")
                    payload = format_graphql_error(async_result.errors[0])  # type: ignore
                    await _send_message(websocket, GraphQLWS.ERROR, payload, operation_id)
                    continue

                # in the future we should get back async gen directly, back compat for now
                disposable, async_gen = _disposable_and_async_gen_from_obs(async_result)

                observables[operation_id] = disposable
                tasks[operation_id] = get_event_loop().create_task(
                    handle_async_results(async_gen, operation_id, websocket)
                )
            elif message_type == GraphQLWS.STOP:
                if operation_id not in observables:
                    return

                observables[operation_id].dispose()
                del observables[operation_id]

                tasks[operation_id].cancel()
                del tasks[operation_id]

    except WebSocketDisconnect:
        pass
    finally:
        for operation_id in observables:
            observables[operation_id].dispose()
            tasks[operation_id].cancel()


async def handle_async_results(results: AsyncGenerator, operation_id: str, websocket: WebSocket):
    try:
        async for result in results:
            payload = {"data": result.data}

            if result.errors:
                payload["errors"] = [format_graphql_error(err) for err in result.errors]

            await _send_message(websocket, GraphQLWS.DATA, payload, operation_id)
    except Exception as error:  # pylint: disable=broad-except
        if not isinstance(error, GraphQLError):
            error = GraphQLError(str(error))

        await _send_message(
            websocket,
            GraphQLWS.DATA,
            {"data": None, "errors": [format_graphql_error(error)]},
            operation_id,
        )

    if (
        websocket.client_state != WebSocketState.DISCONNECTED
        and websocket.application_state != WebSocketState.DISCONNECTED
    ):
        await _send_message(websocket, GraphQLWS.COMPLETE, None, operation_id)


async def _send_message(
    websocket: WebSocket,
    type_: GraphQLWS,
    payload: Any,
    operation_id: str,
) -> None:
    data = {"type": type_, "id": operation_id}

    if payload is not None:
        data["payload"] = payload

    return await websocket.send_json(data)


def _disposable_and_async_gen_from_obs(obs: Observable):
    """
    Compatability layer for legacy Observable to async generator

    This should be removed and subscription resolvers changed to
    return async generators after removal of flask & gevent based dagit.
    """
    queue: Queue = Queue()

    disposable = obs.subscribe(on_next=queue.put_nowait)

    async def async_gen():
        while True:
            i = await queue.get()
            yield i

    return disposable, async_gen()


async def download_debug_file_endpoint(
    context: WorkspaceProcessContext,
    request: Request,
):
    run_id = request.path_params["run_id"]
    run = context.instance.get_run_by_id(run_id)
    debug_payload = DebugRunPayload.build(context.instance, run)

    result = io.BytesIO()
    with gzip.GzipFile(fileobj=result, mode="wb") as file:
        debug_payload.write(file)

    result.seek(0)  # be kind, please rewind

    return StreamingResponse(result, media_type="application/gzip")


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


def create_routes(
    process_context: WorkspaceProcessContext,
    graphql_schema: Schema,
    app_path_prefix: str,
    static_resources_dir: str,
):
    bound_index_endpoint = partial(index_endpoint, static_resources_dir, app_path_prefix)

    return [
        Route("/dagit_info", dagit_info_endpoint),
        Route(
            "/graphql",
            partial(graphql_http_endpoint, graphql_schema, process_context, app_path_prefix),
            name="graphql-http",
            methods=["GET", "POST"],
        ),
        WebSocketRoute(
            "/graphql",
            partial(graphql_ws_endpoint, graphql_schema, process_context),
            name="graphql-ws",
        ),
        # static resources addressed at /static/
        Mount(
            "/static",
            StaticFiles(directory=path.join(static_resources_dir, "./webapp/build/static")),
            name="static",
        ),
        # static resources addressed at /vendor/
        Mount(
            "/vendor",
            StaticFiles(directory=path.join(static_resources_dir, "./webapp/build/vendor")),
            name="vendor",
        ),
        # specific static resources addressed at /
        *create_root_static_endpoints(static_resources_dir),
        # download file endpoints
        Route(
            "/download_debug/{run_id:str}",
            partial(download_debug_file_endpoint, process_context),
        ),
        Route("/{path:path}", bound_index_endpoint),
        Route("/", bound_index_endpoint),
    ]


def create_app(
    process_context: WorkspaceProcessContext,
    debug: bool,
    app_path_prefix: str,
):
    graphql_schema = create_schema()
    return Starlette(
        debug=debug,
        routes=create_routes(
            process_context,
            graphql_schema,
            app_path_prefix,
            path.dirname(__file__),
        ),
    )


def default_app():
    instance = DagsterInstance.get()
    process_context = get_workspace_process_context_from_kwargs(
        instance=instance,
        version=__version__,
        read_only=False,
        kwargs={},
    )
    return create_app(process_context, app_path_prefix="", debug=True)
