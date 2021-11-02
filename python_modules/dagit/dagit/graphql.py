from abc import ABC, abstractmethod
from asyncio import Queue, get_event_loop
from enum import Enum
from typing import Any, AsyncGenerator, Dict, List, Union

from dagit.templates.playground import TEMPLATE
from dagster import check
from graphene import Schema
from graphql.error import GraphQLError
from graphql.error import format_error as format_graphql_error
from graphql.execution import ExecutionResult
from rx import Observable
from starlette import status
from starlette.applications import Starlette
from starlette.concurrency import run_in_threadpool
from starlette.datastructures import QueryParams
from starlette.middleware import Middleware
from starlette.requests import HTTPConnection, Request
from starlette.responses import HTMLResponse, JSONResponse, PlainTextResponse
from starlette.routing import BaseRoute
from starlette.websockets import WebSocket, WebSocketDisconnect, WebSocketState


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


class GraphQLServer(ABC):
    def __init__(self, app_path_prefix: str = ""):
        self._app_path_prefix = app_path_prefix

        self._graphql_schema = self.build_graphql_schema()
        self._graphql_middleware = self.build_graphql_middleware()

    @abstractmethod
    def build_graphql_schema(self) -> Schema:
        raise NotImplementedError()

    @abstractmethod
    def build_graphql_middleware(self) -> list:
        raise NotImplementedError()

    @abstractmethod
    def build_middleware(self) -> List[Middleware]:
        raise NotImplementedError()

    @abstractmethod
    def build_routes(self) -> List[BaseRoute]:
        raise NotImplementedError()

    @abstractmethod
    def make_request_context(self, conn: HTTPConnection):
        raise NotImplementedError()

    async def graphql_http_endpoint(self, request: Request):
        """
        fork of starlette GraphQLApp to allow for
            * our context type (crucial)
            * our GraphiQL playground (could change)
        """

        if request.method == "GET":
            # render graphiql
            if "text/html" in request.headers.get("Accept", ""):
                text = TEMPLATE.replace("{{ app_path_prefix }}", self._app_path_prefix)
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

        result = await run_in_threadpool(  # threadpool = aio event loop
            self._graphql_schema.execute,
            query,
            variables=variables,
            operation_name=operation_name,
            context=self.make_request_context(request),
            middleware=self._graphql_middleware,
        )

        error_data = [format_graphql_error(err) for err in result.errors] if result.errors else None
        response_data = {"data": result.data}
        if error_data:
            response_data["errors"] = error_data
        status_code = status.HTTP_400_BAD_REQUEST if result.errors else status.HTTP_200_OK

        return JSONResponse(response_data, status_code=status_code)

    async def graphql_ws_endpoint(self, websocket: WebSocket):
        """
        Implementation of websocket ASGI endpoint for GraphQL.
        Once we are free of conflicting deps, we should be able to use an impl from
        strawberry-graphql or the like.
        """
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
                        request_context = self.make_request_context(websocket)
                        async_result = self._graphql_schema.execute(
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
                            check.failed(
                                f"Only expect non-async result on error, got {async_result}"
                            )
                        payload = format_graphql_error(async_result.errors[0])  # type: ignore
                        await _send_message(websocket, GraphQLWS.ERROR, payload, operation_id)
                        continue

                    # in the future we should get back async gen directly, back compat for now
                    disposable, async_gen = _disposable_and_async_gen_from_obs(async_result)

                    observables[operation_id] = disposable
                    tasks[operation_id] = get_event_loop().create_task(
                        _handle_async_results(async_gen, operation_id, websocket)
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

    def create_asgi_app(
        self,
        **kwargs,
    ) -> Starlette:
        return Starlette(
            routes=self.build_routes(),
            middleware=self.build_middleware(),
            **kwargs,
        )


async def _handle_async_results(results: AsyncGenerator, operation_id: str, websocket: WebSocket):
    try:
        async for result in results:
            payload = {"data": result.data}

            if result.errors:
                payload["errors"] = [format_graphql_error(err) for err in result.errors]

            await _send_message(websocket, GraphQLWS.DATA, payload, operation_id)
    except Exception as error:
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
