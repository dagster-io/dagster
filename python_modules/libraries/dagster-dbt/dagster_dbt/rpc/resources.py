import json
import platform
import sys
import uuid
from base64 import standard_b64encode as b64
from typing import Any, Dict, List, Optional

import requests
from dagster import Field, IntSource, RetryRequested, StringSource, check, resource

from .utils import is_fatal_code


class DbtRpcClient:
    """A client for a dbt RPC server.

    If you are need a dbt RPC server as a Dagster resource, we recommend that you use
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
        """Constructor

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
        self._logger = logger

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
        return headers

    def _post(self, data: str = None) -> requests.Response:
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
        return response

    def _default_request(self, method: str) -> Dict[str, Any]:
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
            "params": {},
        }
        return data

    def _selection(
        self, *, models: List[str] = None, select: List[str] = None, exclude: List[str] = None
    ) -> Dict[str, str]:
        params = {}
        if models is not None:
            params["models"] = " ".join(set(models))
        if select is not None:
            params["select"] = " ".join(set(select))
        if exclude is not None:
            params["exclude"] = " ".join(set(exclude))

        return params

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
    def logger(self) -> Optional[Any]:
        """Optional[Any]: A property for injecting a logger dependency."""
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

    def poll(
        self, *, request_token: str, logs: bool = False, logs_start: int = 0
    ) -> requests.Response:
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

    def ps(self, *, completed: bool = False) -> requests.Response:
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

    def kill(self, *, task_id: str) -> requests.Response:
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

    def cli(self, *, cli: str, **kwargs) -> requests.Response:
        """Sends a request with CLI syntax to the dbt RPC server, and returns the response.
        For more details, see the dbt docs for `running CLI commands via RPC
        <https://docs.getdbt.com/reference/commands/rpc/#running-a-task-with-cli-syntax>`_.

        Args:
            cli (str): a dbt command in CLI syntax.

        Returns:
            Response: the HTTP response from the dbt RPC server.
        """
        data = self._default_request(method="cli_args")
        data["params"] = {"cli": cli}

        if kwargs is not None:
            data["params"]["task_tags"] = kwargs

        return self._post(data=json.dumps(data))

    def compile(
        self, *, models: List[str] = None, exclude: List[str] = None, **kwargs
    ) -> requests.Response:
        """Sends a request with the method ``compile`` to the dbt RPC server, and returns the
        response. For more details, see the dbt docs for `compiling projects via RPC
        <https://docs.getdbt.com/reference/commands/rpc/#compile-a-project>`_.

        Args:
            models (List[str], optional): the models to include in compilation.
            exclude (List[str]), optional): the models to exclude from compilation.

        Returns:
            Response: the HTTP response from the dbt RPC server.
        """
        data = self._default_request(method="compile")
        data["params"].update(self._selection(models=models, exclude=exclude))

        if kwargs is not None:
            data["params"]["task_tags"] = kwargs

        return self._post(data=json.dumps(data))

    def run(
        self, *, models: List[str] = None, exclude: List[str] = None, **kwargs
    ) -> requests.Response:
        """Sends a request with the method ``run`` to the dbt RPC server, and returns the response.
        For more details, see the dbt docs for the RPC method `run
        <https://docs.getdbt.com/reference/commands/rpc/#run-models>`_.

        Args:
            models (List[str], optional): the models to include in the run.
            exclude (List[str]), optional): the models to exclude from the run.

        Returns:
            Response: the HTTP response from the dbt RPC server.
        """
        data = self._default_request(method="run")
        data["params"].update(self._selection(models=models, exclude=exclude))

        if kwargs is not None:
            data["params"]["task_tags"] = kwargs

        return self._post(data=json.dumps(data))

    def snapshot(
        self, *, select: List[str] = None, exclude: List[str] = None, **kwargs
    ) -> requests.Response:
        """Sends a request with the method ``snapshot`` to the dbt RPC server, and returns the
        response. For more details, see the dbt docs for the command `snapshot
        <https://docs.getdbt.com/reference/commands/snapshot>`_.

        Args:
            select (List[str], optional): the snapshots to include in the run.
            exclude (List[str], optional): the snapshots to exclude from the run.

        Returns:
            Response: the HTTP response from the dbt RPC server.
        """
        data = self._default_request(method="snapshot")
        data["params"].update(self._selection(select=select, exclude=exclude))

        if kwargs is not None:
            data["params"]["task_tags"] = kwargs

        return self._post(data=json.dumps(data))

    def test(
        self,
        *,
        models: List[str] = None,
        exclude: List[str] = None,
        data: bool = True,
        schema: bool = True,
        **kwargs,
    ) -> requests.Response:
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
        payload = self._default_request(method="test")
        payload["params"] = {"data": data, "schema": schema}

        payload["params"].update(self._selection(models=models, exclude=exclude))

        if kwargs is not None:
            payload["params"]["task_tags"] = kwargs

        return self._post(data=json.dumps(payload))

    def seed(self, *, show: bool = False, **kwargs) -> requests.Response:
        """Sends a request with the method ``seed`` to the dbt RPC server, and returns the response.
        For more details, see the dbt docs for the RPC method `seed
        <https://docs.getdbt.com/reference/commands/rpc/#run-seed>`_.

        Args:
            show (bool, optional): If ``True``, then show a sample of the seeded data in the
                response. Defaults to ``False``.

        Returns:
            Response: the HTTP response from the dbt RPC server.
        """
        data = self._default_request(method="seed")
        data["params"] = {"show": show}

        if kwargs is not None:
            data["params"]["task_tags"] = kwargs

        return self._post(data=json.dumps(data))

    def generate_docs(
        self,
        *,
        models: List[str] = None,
        exclude: List[str] = None,
        compile: bool = False,  # pylint: disable=redefined-builtin # TODO
        **kwargs,
    ) -> requests.Response:
        """Sends a request with the method ``docs.generate`` to the dbt RPC server, and returns the
        response. For more details, see the dbt docs for the RPC method `docs.generate
        <https://docs.getdbt.com/reference/commands/rpc/#generate-docs>`_.

        Args:
            models (List[str], optional): the models to include in docs generation.
            exclude (List[str], optional): the models to exclude from docs generation.
            compile (bool, optional): If ``True`` (default), then compile the project before
                generating docs.

        Returns:
            Response: the HTTP response from the dbt RPC server.
        """
        data = self._default_request(method="docs.generate")
        data["params"] = {"compile": compile}

        data["params"].update(self._selection(models=models, exclude=exclude))

        if kwargs is not None:
            data["params"]["task_tags"] = kwargs

        return self._post(data=json.dumps(data))

    def run_operation(
        self, *, macro: str, args: Optional[Dict[str, Any]] = None, **kwargs
    ) -> requests.Response:
        """Sends a request with the method ``run-operation`` to the dbt RPC server, and returns the
        response. For more details, see the dbt docs for the command `run-operation
        <https://docs.getdbt.com/reference/commands/run-operation>`_.

        Args:
            macro (str): the dbt macro to invoke.
            args (Dict[str, Any], optional): the keyword arguments to be supplied to the macro.

        Returns:
            Response: the HTTP response from the dbt RPC server.
        """
        data = self._default_request(method="run-operation")
        data["params"] = {"macro": macro}

        if args is not None:
            data["params"]["args"] = args

        if kwargs is not None:
            data["params"]["task_tags"] = kwargs

        return self._post(data=json.dumps(data))

    def snapshot_freshness(
        self, *, select: Optional[List[str]] = None, **kwargs
    ) -> requests.Response:
        """Sends a request with the method ``snapshot-freshness`` to the dbt RPC server, and returns
        the response. For more details, see the dbt docs for the command `source snapshot-freshness
        <https://docs.getdbt.com/reference/commands/source#dbt-source-snapshot-freshness>`_.

        Args:
            select (List[str], optional): the models to include in calculating snapshot freshness.

        Returns:
            Response: the HTTP response from the dbt RPC server.
        """
        data = self._default_request(method="snapshot-freshness")
        data["params"].update(self._selection(select=select))

        if kwargs is not None:
            data["params"]["task_tags"] = kwargs

        return self._post(data=json.dumps(data))

    def compile_sql(self, *, sql: str, name: str) -> requests.Response:
        """Sends a request with the method ``compile_sql`` to the dbt RPC server, and returns the
        response. For more details, see the dbt docs for `compiling SQL via RPC
        <https://docs.getdbt.com/reference/commands/rpc#compiling-a-query>`_.

        Args:
            sql (str): the SQL to compile in base-64 encoding.
            name (str): a name for the compiled SQL.

        Returns:
            Response: the HTTP response from the dbt RPC server.
        """
        data = self._default_request(method="compile_sql")
        data["params"] = {"sql": b64(sql.encode("utf-8")).decode("utf-8"), "name": name}
        return self._post(data=json.dumps(data))

    def run_sql(self, *, sql: str, name: str) -> requests.Response:
        """Sends a request with the method ``run_sql`` to the dbt RPC server, and returns the
        response. For more details, see the dbt docs for `running SQL via RPC
        <https://docs.getdbt.com/reference/commands/rpc#executing-a-query>`_.

        Args:
            sql (str): the SQL to run in base-64 encoding.
            name (str): a name for the compiled SQL.

        Returns:
            Response: the HTTP response from the dbt RPC server.
        """
        data = self._default_request(method="run_sql")
        data["params"] = {"sql": b64(sql.encode("utf-8")).decode("utf-8"), "name": name}
        return self._post(data=json.dumps(data))


@resource(
    description="A resource representing a dbt RPC client.",
    config_schema={
        "host": Field(StringSource),
        "port": Field(IntSource, is_required=False, default_value=8580),
    },
)
def dbt_rpc_resource(context) -> DbtRpcClient:
    """This resource defines a dbt RPC client.

    To configure this resource, we recommend using the `configured
    <https://docs.dagster.io/overview/configuration#configured>`_ method.

    Examples:

    .. code-block:: python

        custom_dbt_rpc_resource = dbt_rpc_resource.configured({"host": "80.80.80.80","port": 8080,})

        @pipeline(mode_defs=[ModeDefinition(resource_defs={"dbt_rpc": custom_dbt_rpc_resource})])
        def dbt_rpc_pipeline():
            # Run solids with `required_resource_keys={"dbt_rpc", ...}`.

    """
    return DbtRpcClient(host=context.resource_config["host"], port=context.resource_config["port"])


local_dbt_rpc_resource = dbt_rpc_resource.configured({"host": "0.0.0.0", "port": 8580})
local_dbt_rpc_resource.__doc__ = """This resource defines a dbt RPC client for an RPC server running
on 0.0.0.0:8580."""
