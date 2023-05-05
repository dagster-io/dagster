from abc import ABC, abstractmethod
from asyncio import Task, get_event_loop
from enum import Enum
from typing import Any, AsyncGenerator, Dict, List, Optional, Sequence, Tuple, Union, cast

import dagster._check as check
from dagster._serdes import pack_value
from dagster._seven import json
from dagster._utils.error import serializable_error_info_from_exc_info
from dagster_graphql.implementation.utils import ErrorCapture
from graphene import Schema
from graphql import GraphQLError, GraphQLFormattedError
from graphql.execution import ExecutionResult
from starlette import status
from starlette.applications import Starlette
from starlette.concurrency import run_in_threadpool
from starlette.datastructures import QueryParams
from starlette.middleware import Middleware
from starlette.requests import HTTPConnection, Request
from starlette.responses import HTMLResponse, JSONResponse, PlainTextResponse
from starlette.routing import BaseRoute
from starlette.websockets import WebSocket, WebSocketDisconnect, WebSocketState

from dagit.templates.playground import TEMPLATE


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
        ...

    @abstractmethod
    def build_graphql_middleware(self) -> list:
        ...

    @abstractmethod
    def build_middleware(self) -> List[Middleware]:
        ...

    @abstractmethod
    def build_routes(self) -> List[BaseRoute]:
        ...

    @abstractmethod
    def make_request_context(self, conn: HTTPConnection):
        ...

    def handle_graphql_errors(self, errors: Sequence[GraphQLError]):
        results = []
        for err in errors:
            fmtd = err.formatted
            if err.original_error and err.original_error.__traceback__:
                serializable_error = serializable_error_info_from_exc_info(
                    exc_info=(
                        type(err.original_error),
                        err.original_error,
                        err.original_error.__traceback__,
                    )
                )
                fmtd["extensions"] = {
                    **fmtd.get("extensions", {}),
                    "errorInfo": pack_value(serializable_error),
                }

            results.append(fmtd)

        return results

    async def graphql_http_endpoint(self, request: Request):
        """Fork of starlette GraphQLApp.

        Allows for:
        * our context type (crucial)
        * our GraphiQL playground (could change).
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
                try:
                    data = await request.json()
                except json.JSONDecodeError:
                    body = await request.body()
                    return PlainTextResponse(
                        f"GraphQL request is invalid JSON:\n{body.decode()}",
                        status_code=status.HTTP_400_BAD_REQUEST,
                    )
            elif "application/graphql" in content_type:
                body = await request.body()
                text = body.decode()
                data = {"query": text}
            else:
                data = request.query_params
        else:
            return PlainTextResponse(
                "Method Not Allowed", status_code=status.HTTP_405_METHOD_NOT_ALLOWED
            )

        query = data.get("query")
        variables: Union[Optional[str], Dict[str, Any]] = data.get("variables")
        operation_name = data.get("operationName")

        if query is None:
            return PlainTextResponse(
                "No GraphQL query found in the request",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        if isinstance(variables, str):
            try:
                variables = cast(Dict[str, Any], json.loads(variables))
            except json.JSONDecodeError:
                return PlainTextResponse(
                    (
                        "Malformed GraphQL variables. Passed as string but not valid"
                        f" JSON:\n{variables}"
                    ),
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

        captured_errors: List[Exception] = []
        with ErrorCapture.watch(captured_errors.append):
            result = await self.execute_graphql_request(request, query, variables, operation_name)

        response_data = {"data": result.data}

        if result.errors:
            response_data["errors"] = self.handle_graphql_errors(result.errors)

        return JSONResponse(
            response_data,
            status_code=self._determine_status_code(
                resolver_errors=result.errors,
                captured_errors=captured_errors,
            ),
        )

    async def graphql_ws_endpoint(self, websocket: WebSocket):
        """Implementation of websocket ASGI endpoint for GraphQL.
        Once we are free of conflicting deps, we should be able to use an impl from
        strawberry-graphql or the like.
        """
        tasks: Dict[str, Task] = {}

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
                    data = message["payload"]

                    task, error_payload = await self.execute_graphql_subscription(
                        websocket=websocket,
                        operation_id=operation_id,
                        query=data["query"],
                        variables=data.get("variables"),
                        operation_name=data.get("operation_name"),
                    )
                    if error_payload:
                        await _send_message(websocket, GraphQLWS.ERROR, error_payload, operation_id)
                        continue

                    assert task is not None

                    tasks[operation_id] = task

                elif message_type == GraphQLWS.STOP:
                    if operation_id not in tasks:
                        return

                    tasks[operation_id].cancel()
                    del tasks[operation_id]

        except WebSocketDisconnect:
            pass
        finally:
            for operation_id in tasks:
                tasks[operation_id].cancel()

    async def execute_graphql_request(
        self,
        request: Request,
        query: str,
        variables: Optional[Dict[str, Any]],
        operation_name: Optional[str],
    ) -> ExecutionResult:
        # use run_in_threadpool since underlying schema is sync
        return await run_in_threadpool(
            self._graphql_schema.execute,
            query,
            variables=variables,
            operation_name=operation_name,
            context=self.make_request_context(request),
            middleware=self._graphql_middleware,
        )

    async def execute_graphql_subscription(
        self,
        websocket: WebSocket,
        operation_id: str,
        query: str,
        variables: Optional[Dict[str, Any]],
        operation_name: Optional[str],
    ) -> Tuple[Optional[Task], Optional[GraphQLFormattedError]]:
        request_context = self.make_request_context(websocket)
        try:
            async_result = await self._graphql_schema.subscribe(
                query,
                variables=variables,
                operation_name=operation_name,
                context=request_context,
            )
        except GraphQLError as error:
            error_payload = error.formatted
            return None, error_payload

        if isinstance(async_result, ExecutionResult):
            if not async_result.errors:
                check.failed(f"Only expect non-async result on error, got {async_result}")
            handled_errors = self.handle_graphql_errors(async_result.errors)
            # return only one entry for subscription response
            return None, handled_errors[0]

        # in the future we should get back async gen directly, back compat for now
        task = get_event_loop().create_task(
            _handle_async_results(async_result, operation_id, websocket)
        )

        return task, None

    def create_asgi_app(
        self,
        **kwargs,
    ) -> Starlette:
        return Starlette(
            routes=self.build_routes(),
            middleware=self.build_middleware(),
            **kwargs,
        )

    def _determine_status_code(
        self,
        resolver_errors: Optional[List[GraphQLError]],
        captured_errors: List[Exception],
    ) -> int:
        server_error = False
        user_error = False

        if resolver_errors:
            for error in resolver_errors:
                # if thrown from a field, has an original error
                if error.original_error:
                    server_error = True
                else:
                    # syntax error, invalid query, etc
                    user_error = True

        if captured_errors:
            server_error = True

        if server_error:
            return status.HTTP_500_INTERNAL_SERVER_ERROR

        if user_error:
            return status.HTTP_400_BAD_REQUEST

        return status.HTTP_200_OK


async def _handle_async_results(results: AsyncGenerator, operation_id: str, websocket: WebSocket):
    try:
        async for result in results:
            payload = {"data": result.data}

            if result.errors:
                payload["errors"] = [err.formatted for err in result.errors]

            await _send_message(websocket, GraphQLWS.DATA, payload, operation_id)
    except Exception as error:
        if not isinstance(error, GraphQLError):
            error = GraphQLError(str(error))

        await _send_message(
            websocket,
            GraphQLWS.DATA,
            {"data": None, "errors": [error.formatted]},
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

    # guard against async code still flushing messages post disconnect
    if (
        websocket.client_state != WebSocketState.DISCONNECTED
        and websocket.application_state != WebSocketState.DISCONNECTED
    ):
        await websocket.send_json(data)
