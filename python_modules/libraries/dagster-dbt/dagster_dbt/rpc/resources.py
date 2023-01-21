import json
import logging
import platform
import sys
import time
import uuid
from base64 import standard_b64encode as b64
from typing import Any, Dict, Mapping, Optional, Sequence, cast

import requests
from dagster import (
    Failure,
    Field,
    IntSource,
    RetryRequested,
    StringSource,
    _check as check,
    resource,
)
from dagster._core.definitions.resource_definition import ResourceDefinition
from dagster._core.utils import coerce_valid_log_level

from ..dbt_resource import DbtResource
from .types import DbtRpcOutput
from .utils import is_fatal_code


class DbtRpcResource(DbtResource):
    """A client for a dbt RPC server.

    To use this as a dagster resource, we recommend using
    :func:`dbt_rpc_resource <dagster_dbt.dbt_rpc_resource>`.
    """

    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 8580,
        jsonrpc_version: str = "2.0",
        logger: Optional[Any] = None,
        **_,
    ):
        """Constructor.

        Args:
            host (str): The IP address of the host of the dbt RPC server. Default is ``"0.0.0.0"``.
            port (int): The port of the dbt RPC server. Default is ``8580``.
            jsonrpc_version (str): The JSON-RPC version to send in RPC requests.
                Default is ``"2.0"``.
            logger (Optional[Any]): A property for injecting a logger dependency.
                Default is ``None``.
        """
        check.str_param(host, "host")
        check.int_param(port, "port")
        check.str_param(jsonrpc_version, "jsonrpc_version")

        self._host = host
        self._port = port
        self._jsonrpc_version = jsonrpc_version
        super().__init__(logger)

    @staticmethod
    def _construct_user_agent() -> str:
        """A helper method to construct a standard User-Agent string to be used in HTTP request
        headers.

        Returns:
            str: The constructed User-Agent value.
        """
        client = "dagster/dbt-rpc-client"
        python_version = (
            f"Python/{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        )
        system_info = f"{platform.system()}/{platform.release()}"
        user_agent = " ".join([python_version, client, system_info])
        return user_agent

    def _construct_headers(self) -> Dict[str, str]:
        """Constructs a standard set of headers for HTTP requests.

        Returns:
            Dict[str, str]: The HTTP request headers.
        """
        headers = requests.utils.default_headers()
        headers["User-Agent"] = self._construct_user_agent()
        headers["Content-Type"] = "application/json"
        headers["Accept"] = "application/json"
        return cast(Dict[str, str], headers)

    def _post(self, data: Optional[str] = None) -> DbtRpcOutput:
        """Constructs and sends a POST request to the dbt RPC server.

        Returns:
            Response: the HTTP response from the dbt RPC server.
        """
        headers = self._construct_headers()
        try:
            response = requests.post(self.url, headers=headers, data=data)
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            if is_fatal_code(e):
                raise e
            else:
                raise RetryRequested(max_retries=5, seconds_to_wait=30)
        return DbtRpcOutput(response)

    def _get_result(self, data: Optional[str] = None) -> DbtRpcOutput:
        """Constructs and sends a POST request to the dbt RPC server.

        Returns:
            Response: the HTTP response from the dbt RPC server.
        """
        return self._post(data)

    def _default_request(
        self, method: str, params: Optional[Mapping[str, Any]] = None
    ) -> Dict[str, Any]:
        """Constructs a standard HTTP request body, to be sent to a dbt RPC server.

        Args:
            method (str): a dbt RPC method.

        Returns:
            Dict: the constructed HTTP request body.
        """
        data = {
            "jsonrpc": self.jsonrpc_version,
            "method": method,
            "id": str(uuid.uuid1()),
            "params": params or {},
        }
        return data

    @property
    def host(self) -> str:
        """str: The IP address of the host of the dbt RPC server."""
        return self._host

    @property
    def port(self) -> int:
        """int: The port of the dbt RPC server."""
        return self._port

    @property
    def jsonrpc_version(self) -> str:
        """str: The JSON-RPC version to send in RPC requests."""
        return self._jsonrpc_version

    @property
    def logger(self) -> logging.Logger:
        """logging.Logger: A property for injecting a logger dependency."""
        return self._logger

    @property
    def url(self) -> str:
        """str: The URL for sending dbt RPC requests."""
        return f"http://{self.host}:{self.port}/jsonrpc"

    def status(self):
        """Sends a request with the method ``status`` to the dbt RPC server, and returns the
        response. For more details, see the dbt docs for the RPC method `status
        <https://docs.getdbt.com/reference/commands/rpc/#status>`_.

        Returns:
            Response: the HTTP response from the dbt RPC server.
        """
        data = self._default_request(method="status")
        return self._post(data=json.dumps(data))

    def ls(
        self,
        select: Optional[Sequence[str]] = None,
        models: Optional[Sequence[str]] = None,
        exclude: Optional[Sequence[str]] = None,
        **kwargs,
    ) -> DbtRpcOutput:
        """Sends a request with the method ``list`` to the dbt RPC server, and returns the
        response. For more details, see the dbt docs for `list
        <https://docs.getdbt.com/reference/commands/rpc/#list>`_.

        Args:
            select (List[str], optional): the resources to include in the output.
            models (List[str], optional): the models to include in the output.
            exclude (List[str]), optional): the resources to exclude from compilation.

        Returns:
            Response: the HTTP response from the dbt RPC server.
        """
        explicit_params = dict(models=models, exclude=exclude)
        params = self._format_params({**explicit_params, **kwargs})
        data = self._default_request(method="list", params=params)

        return self._get_result(data=json.dumps(data))

    def poll(self, request_token: str, logs: bool = False, logs_start: int = 0) -> DbtRpcOutput:
        """Sends a request with the method ``poll`` to the dbt RPC server, and returns the response.
        For more details, see the dbt docs for the RPC method `poll
        <https://docs.getdbt.com/reference/commands/rpc/#poll>`_.

        Args:
            request_token (str): the token to poll responses for.
            logs (bool): Whether logs should be returned in the response. Defaults to ``False``.
            logs_start (int): The zero-indexed log line to fetch logs from. Defaults to ``0``.

        Returns:
            Response: the HTTP response from the dbt RPC server.
        """
        data = self._default_request(method="poll")
        data["params"] = {"request_token": request_token, "logs": logs, "logs_start": logs_start}
        return self._post(data=json.dumps(data))

    def ps(self, completed: bool = False) -> DbtRpcOutput:
        """Sends a request with the method ``ps`` to the dbt RPC server, and returns the response.
        For more details, see the dbt docs for the RPC method `ps
        <https://docs.getdbt.com/reference/commands/rpc/#ps>`_.

        Args:
            compelted (bool): If ``True``, then also return completed tasks. Defaults to ``False``.

        Returns:
            Response: the HTTP response from the dbt RPC server.
        """
        data = self._default_request(method="ps")
        data["params"] = {"completed": completed}
        return self._post(data=json.dumps(data))

    def kill(self, task_id: str) -> DbtRpcOutput:
        """Sends a request with the method ``kill`` to the dbt RPC server, and returns the response.
        For more details, see the dbt docs for the RPC method `kill
        <https://docs.getdbt.com/reference/commands/rpc/#kill>`_.

        Args:
            task_id (str): the ID of the task to terminate.

        Returns:
            Response: the HTTP response from the dbt RPC server.
        """
        data = self._default_request(method="kill")
        data["params"] = {"task_id": task_id}
        return self._post(data=json.dumps(data))

    def cli(self, command: str, **kwargs) -> DbtRpcOutput:
        """Sends a request with CLI syntax to the dbt RPC server, and returns the response.
        For more details, see the dbt docs for `running CLI commands via RPC
        <https://docs.getdbt.com/reference/commands/rpc/#running-a-task-with-cli-syntax>`_.

        Args:
            cli (str): a dbt command in CLI syntax.

        Returns:
            Response: the HTTP response from the dbt RPC server.
        """
        params = self._format_params({"cli": command, **kwargs})
        data = self._default_request(method="cli_args", params=params)

        return self._get_result(data=json.dumps(data))

    def compile(
        self,
        models: Optional[Sequence[str]] = None,
        exclude: Optional[Sequence[str]] = None,
        **kwargs,
    ) -> DbtRpcOutput:
        """Sends a request with the method ``compile`` to the dbt RPC server, and returns the
        response. For more details, see the dbt docs for `compiling projects via RPC
        <https://docs.getdbt.com/reference/commands/rpc/#compile-a-project>`_.

        Args:
            models (List[str], optional): the models to include in compilation.
            exclude (List[str]), optional): the models to exclude from compilation.

        Returns:
            Response: the HTTP response from the dbt RPC server.
        """
        explicit_params = dict(models=models, exclude=exclude)
        params = self._format_params({**explicit_params, **kwargs})
        data = self._default_request(method="compile", params=params)

        return self._get_result(data=json.dumps(data))

    def run(
        self,
        models: Optional[Sequence[str]] = None,
        exclude: Optional[Sequence[str]] = None,
        **kwargs,
    ) -> DbtRpcOutput:
        """Sends a request with the method ``run`` to the dbt RPC server, and returns the response.
        For more details, see the dbt docs for the RPC method `run
        <https://docs.getdbt.com/reference/commands/rpc/#run-models>`_.

        Args:
            models (List[str], optional): the models to include in the run.
            exclude (List[str]), optional): the models to exclude from the run.

        Returns:
            Response: the HTTP response from the dbt RPC server.
        """
        explicit_params = dict(models=models, exclude=exclude)
        params = self._format_params({**explicit_params, **kwargs})
        data = self._default_request(method="run", params=params)

        return self._get_result(data=json.dumps(data))

    def snapshot(
        self,
        select: Optional[Sequence[str]] = None,
        exclude: Optional[Sequence[str]] = None,
        **kwargs,
    ) -> DbtRpcOutput:
        """Sends a request with the method ``snapshot`` to the dbt RPC server, and returns the
        response. For more details, see the dbt docs for the command `snapshot
        <https://docs.getdbt.com/reference/commands/snapshot>`_.

        Args:
            select (List[str], optional): the snapshots to include in the run.
            exclude (List[str], optional): the snapshots to exclude from the run.

        Returns:
            Response: the HTTP response from the dbt RPC server.
        """
        explicit_params = dict(select=select, exclude=exclude)
        params = self._format_params({**explicit_params, **kwargs})
        data = self._default_request(method="snapshot", params=params)

        return self._get_result(data=json.dumps(data))

    def test(
        self,
        models: Optional[Sequence[str]] = None,
        exclude: Optional[Sequence[str]] = None,
        data: bool = True,
        schema: bool = True,
        **kwargs,
    ) -> DbtRpcOutput:
        """Sends a request with the method ``test`` to the dbt RPC server, and returns the response.
        For more details, see the dbt docs for the RPC method `test
        <https://docs.getdbt.com/reference/commands/rpc/#run-test>`_.

        Args:
            models (List[str], optional): the models to include in testing.
            exclude (List[str], optional): the models to exclude from testing.
            data (bool, optional): If ``True`` (default), then run data tests.
            schema (bool, optional): If ``True`` (default), then run schema tests.

        Returns:
            Response: the HTTP response from the dbt RPC server.
        """
        explicit_params = dict(models=models, exclude=exclude, data=data, schema=schema)
        params = self._format_params({**explicit_params, **kwargs})
        data = self._default_request(method="test", params=params)

        return self._get_result(data=json.dumps(data))

    def seed(
        self,
        show: bool = False,
        select: Optional[Sequence[str]] = None,
        exclude: Optional[Sequence[str]] = None,
        **kwargs,
    ) -> DbtRpcOutput:
        """Sends a request with the method ``seed`` to the dbt RPC server, and returns the response.
        For more details, see the dbt docs for the RPC method `seed
        <https://docs.getdbt.com/reference/commands/rpc/#run-seed>`_.

        Args:
            show (bool, optional): If ``True``, then show a sample of the seeded data in the
                response. Defaults to ``False``.
            select (List[str], optional): the snapshots to include in the run.
            exclude (List[str], optional): the snapshots to exclude from the run.

        Returns:
            Response: the HTTP response from the dbt RPC server.
        """
        data = self._default_request(method="seed")
        data["params"] = {"show": show}

        if kwargs is not None:
            data["params"]["task_tags"] = kwargs

        return self._get_result(data=json.dumps(data))

    def generate_docs(
        self,
        compile_project: bool = False,
        **kwargs,
    ) -> DbtRpcOutput:
        """Sends a request with the method ``docs.generate`` to the dbt RPC server, and returns the
        response. For more details, see the dbt docs for the RPC method `docs.generate
        <https://docs.getdbt.com/reference/commands/rpc/#generate-docs>`_.

        Args:
            compile_project (bool, optional): If true, compile the project before generating a catalog.

        """
        explicit_params = dict(compile=compile_project)
        params = self._format_params({**explicit_params, **kwargs})
        data = self._default_request(method="docs.generate", params=params)

        return self._get_result(data=json.dumps(data))

    def run_operation(
        self, macro: str, args: Optional[Mapping[str, Any]] = None, **kwargs
    ) -> DbtRpcOutput:
        """Sends a request with the method ``run-operation`` to the dbt RPC server, and returns the
        response. For more details, see the dbt docs for the command `run-operation
        <https://docs.getdbt.com/reference/commands/run-operation>`_.

        Args:
            macro (str): the dbt macro to invoke.
            args (Dict[str, Any], optional): the keyword arguments to be supplied to the macro.

        Returns:
            Response: the HTTP response from the dbt RPC server.
        """
        explicit_params = dict(macro=macro, args=args)
        params = self._format_params({**explicit_params, **kwargs})
        data = self._default_request(method="run-operation", params=params)

        return self._get_result(data=json.dumps(data))

    def snapshot_freshness(self, select: Optional[Sequence[str]] = None, **kwargs) -> DbtRpcOutput:
        """Sends a request with the method ``snapshot-freshness`` to the dbt RPC server, and returns
        the response. For more details, see the dbt docs for the command `source snapshot-freshness
        <https://docs.getdbt.com/reference/commands/source#dbt-source-snapshot-freshness>`_.

        Args:
            select (List[str], optional): the models to include in calculating snapshot freshness.

        Returns:
            Response: the HTTP response from the dbt RPC server.
        """
        explicit_params = dict(select=select)
        params = self._format_params({**explicit_params, **kwargs})
        data = self._default_request(method="snapshot-freshness", params=params)

        return self._get_result(data=json.dumps(data))

    def compile_sql(self, sql: str, name: str) -> DbtRpcOutput:
        """Sends a request with the method ``compile_sql`` to the dbt RPC server, and returns the
        response. For more details, see the dbt docs for `compiling SQL via RPC
        <https://docs.getdbt.com/reference/commands/rpc#compiling-a-query>`_.

        Args:
            sql (str): the SQL to compile in base-64 encoding.
            name (str): a name for the compiled SQL.

        Returns:
            Response: the HTTP response from the dbt RPC server.
        """
        explicit_params = dict(sql=b64(sql.encode("utf-8")).decode("utf-8"), name=name)
        params = self._format_params(explicit_params)
        data = self._default_request(method="compile_sql", params=params)

        return self._get_result(data=json.dumps(data))

    def run_sql(self, sql: str, name: str) -> DbtRpcOutput:
        """Sends a request with the method ``run_sql`` to the dbt RPC server, and returns the
        response. For more details, see the dbt docs for `running SQL via RPC
        <https://docs.getdbt.com/reference/commands/rpc#executing-a-query>`_.

        Args:
            sql (str): the SQL to run in base-64 encoding.
            name (str): a name for the compiled SQL.

        Returns:
            Response: the HTTP response from the dbt RPC server.
        """
        explicit_params = dict(sql=b64(sql.encode("utf-8")).decode("utf-8"), name=name)
        params = self._format_params(explicit_params)
        data = self._default_request(method="run_sql", params=params)

        return self._get_result(data=json.dumps(data))

    def build(self, select: Optional[Sequence[str]] = None, **kwargs) -> DbtRpcOutput:
        """
        Run the ``build`` command on a dbt project. kwargs are passed in as additional parameters.

        Args:
            select (List[str], optional): the models/resources to include in the run.

        Returns:
            DbtOutput: object containing parsed output from dbt
        """
        ...  # pylint: disable=unnecessary-ellipsis
        raise NotImplementedError()

    def get_run_results_json(self, **kwargs) -> Optional[Mapping[str, Any]]:
        """
        Get a parsed version of the run_results.json file for the relevant dbt project.

        Returns:
            Dict[str, Any]: dictionary containing the parsed contents of the run_results json file
                for this dbt project.
        """
        ...  # pylint: disable=unnecessary-ellipsis
        raise NotImplementedError()

    def get_manifest_json(self, **kwargs) -> Optional[Mapping[str, Any]]:
        """
        Get a parsed version of the manifest.json file for the relevant dbt project.

        Returns:
            Dict[str, Any]: dictionary containing the parsed contents of the manifest json file
                for this dbt project.
        """
        ...  # pylint: disable=unnecessary-ellipsis
        raise NotImplementedError()


class DbtRpcSyncResource(DbtRpcResource):
    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 8580,
        jsonrpc_version: str = "2.0",
        logger: Optional[Any] = None,
        poll_interval: int = 1,
        **_,
    ):
        """Constructor.

        Args:
            host (str): The IP address of the host of the dbt RPC server. Default is ``"0.0.0.0"``.
            port (int): The port of the dbt RPC server. Default is ``8580``.
            jsonrpc_version (str): The JSON-RPC version to send in RPC requests.
                Default is ``"2.0"``.
            logger (Optional[Any]): A property for injecting a logger dependency.
                Default is ``None``.
            poll_interval (int): The polling interval in seconds.
        """
        super().__init__(host, port, jsonrpc_version, logger)
        self.poll_interval = poll_interval

    def _get_result(self, data: Optional[str] = None) -> DbtRpcOutput:
        """Sends a request to the dbt RPC server and continuously polls for the status of a request
        until the state is ``success``.
        """
        out = super()._get_result(data)
        request_token: str = check.not_none(out.result.get("request_token"))

        logs_start = 0

        elapsed_time = -1
        current_state = None

        while True:
            out = self.poll(
                request_token=request_token,
                logs=True,
                logs_start=logs_start,
            )
            logs = out.result.get("logs", [])
            for log in logs:
                self.logger.log(
                    msg=log["message"],
                    level=coerce_valid_log_level(log.get("levelname", "INFO")),
                    extra=log.get("extra"),
                )
            logs_start += len(logs)

            current_state = out.result.get("state")
            # Stop polling if request's state is no longer "running".
            if current_state != "running":
                break

            elapsed_time = out.result.get("elapsed", 0)
            # Sleep for the configured time interval before polling again.
            time.sleep(self.poll_interval)

        if current_state != "success":
            raise Failure(
                description=(
                    f"Request {request_token} finished with state '{current_state}' in "
                    f"{elapsed_time} seconds"
                ),
            )

        return out


@resource(
    description="A resource representing a dbt RPC client.",
    config_schema={
        "host": Field(StringSource),
        "port": Field(IntSource, is_required=False, default_value=8580),
    },
)
def dbt_rpc_resource(context) -> DbtRpcResource:
    """This resource defines a dbt RPC client.

    To configure this resource, we recommend using the `configured
    <https://docs.dagster.io/concepts/configuration/configured>`_ method.

    Examples:
        .. code-block:: python

            from dagster_dbt import dbt_rpc_resource

            custom_dbt_rpc_resource = dbt_rpc_resource.configured({"host": "80.80.80.80","port": 8080,})

            @job(resource_defs={"dbt_rpc": custom_dbt_rpc_sync_resource})
            def dbt_rpc_job():
                # Run ops with `required_resource_keys={"dbt_rpc", ...}`.
    """
    return DbtRpcResource(
        host=context.resource_config["host"], port=context.resource_config["port"]
    )


@resource(
    description="A resource representing a synchronous dbt RPC client.",
    config_schema={
        "host": Field(StringSource),
        "port": Field(IntSource, is_required=False, default_value=8580),
        "poll_interval": Field(IntSource, is_required=False, default_value=1),
    },
)
def dbt_rpc_sync_resource(
    context,
) -> DbtRpcSyncResource:
    """This resource defines a synchronous dbt RPC client, which sends requests to a dbt RPC server,
    and waits for the request to complete before returning.

    To configure this resource, we recommend using the `configured
    <https://docs.dagster.io/concepts/configuration/configured>`_ method.

    Examples:
        .. code-block:: python

            from dagster_dbt import dbt_rpc_sync_resource

            custom_sync_dbt_rpc_resource = dbt_rpc_sync_resource.configured({"host": "80.80.80.80","port": 8080,})

            @job(resource_defs={"dbt_rpc": custom_dbt_rpc_sync_resource})
            def dbt_rpc_sync_job():
                # Run ops with `required_resource_keys={"dbt_rpc", ...}`.
    """
    return DbtRpcSyncResource(
        host=context.resource_config["host"],
        port=context.resource_config["port"],
        poll_interval=context.resource_config["poll_interval"],
    )


local_dbt_rpc_resource = cast(
    ResourceDefinition, dbt_rpc_resource.configured({"host": "0.0.0.0", "port": 8580})
)
local_dbt_rpc_resource.__doc__ = """This resource defines a dbt RPC client for an RPC server running
on 0.0.0.0:8580."""
