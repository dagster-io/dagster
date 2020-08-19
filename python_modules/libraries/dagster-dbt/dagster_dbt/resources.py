import json
import platform
import sys
import uuid
from base64 import standard_b64encode as b64
from typing import Any, Dict, List, Optional

import attr
import requests

from dagster import Field, IntSource, RetryRequested, StringSource, resource

from .utils import is_fatal_code


@attr.s
class DbtRpcClient(object):

    host: str = attr.ib(default="0.0.0.0")
    port: int = attr.ib(validator=attr.validators.instance_of(int), default=8580)
    jsonrpc_version: str = attr.ib(validator=attr.validators.instance_of(str), default="2.0")
    url: str = attr.ib(init=False)

    def __attrs_post_init__(self):
        self.url = f"http://{self.host}:{self.port}/jsonrpc"

    @staticmethod
    def _construct_user_agent() -> str:
        """Constructs a standard User Agent string to be used in headers for HTTP requests."""
        client = "dagster/dbt-rpc-client"
        python_version = (
            f"Python/{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        )
        system_info = f"{platform.system()}/{platform.release()}"
        user_agent = " ".join([python_version, client, system_info])
        return user_agent

    def _construct_headers(self) -> Dict:
        """Constructs a standard set of headers for HTTP requests."""
        headers = requests.utils.default_headers()
        headers["User-Agent"] = self._construct_user_agent()
        headers["Content-Type"] = "application/json"
        headers["Accept"] = "application/json"
        return headers

    def _post(self, data: str = None) -> requests.Response:
        """Constructs a standard way of making a POST request to the dbt RPC server."""
        headers = self._construct_headers()
        try:
            response = requests.post(self.url, headers=headers, data=data)
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            if is_fatal_code(e):
                raise e
            else:
                raise RetryRequested(max_retries=5, seconds_to_wait=30)  # TODO backoff logic
        return response

    def _default_request(self, method: str) -> Dict:
        data = {
            "jsonrpc": self.jsonrpc_version,
            "method": method,
            "id": str(uuid.uuid1()),
            "params": {},
        }
        return data

    def _selection(
        self, *, models: List[str] = None, select: List[str] = None, exclude: List[str] = None
    ) -> Dict:
        params = {}
        if models is not None:
            params["models"] = " ".join(set(models))
        if select is not None:
            params["select"] = " ".join(set(select))
        if exclude is not None:
            params["exclude"] = " ".join(set(exclude))

        return params

    def status(self) -> requests.Response:
        data = self._default_request(method="status")
        return self._post(data=json.dumps(data))

    def poll(
        self, *, request_token: str, logs: bool = False, logs_start: int = 0
    ) -> requests.Response:
        data = self._default_request(method="poll")
        data["params"] = {"request_token": request_token, "logs": logs, "logs_start": logs_start}
        return self._post(data=json.dumps(data))

    def ps(self, *, completed: bool = False) -> requests.Response:
        "Lists running and completed processes executed by the RPC server."
        data = self._default_request(method="ps")
        data["params"] = {"completed": completed}
        return self._post(data=json.dumps(data))

    def kill(self, *, task_id: str) -> requests.Response:
        "Terminates a running RPC task."
        data = self._default_request(method="kill")
        data["params"] = {"task_id": task_id}
        return self._post(data=json.dumps(data))

    def cli(self, *, cli: str, **kwargs) -> requests.Response:
        "Terminates a running RPC task."
        data = self._default_request(method="cli_args")
        data["params"] = {"cli": cli}

        if kwargs is not None:
            data["params"]["task_tags"] = kwargs

        return self._post(data=json.dumps(data))

    def compile(
        self, *, models: List[str] = None, exclude: List[str] = None, **kwargs
    ) -> requests.Response:
        "Runs a dbt compile command."
        data = self._default_request(method="compile")
        data["params"].update(self._selection(models=models, exclude=exclude))

        if kwargs is not None:
            data["params"]["task_tags"] = kwargs

        return self._post(data=json.dumps(data))

    def run(
        self, *, models: List[str] = None, exclude: List[str] = None, **kwargs
    ) -> requests.Response:
        "Runs a dbt run command."
        data = self._default_request(method="run")
        data["params"].update(self._selection(models=models, exclude=exclude))

        if kwargs is not None:
            data["params"]["task_tags"] = kwargs

        return self._post(data=json.dumps(data))

    def snapshot(
        self, *, select: List[str] = None, exclude: List[str] = None, **kwargs
    ) -> requests.Response:
        "Runs a dbt snapshot command."
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
        **kwargs
    ) -> requests.Response:
        payload = self._default_request(method="test")
        payload["params"] = {"data": data, "schema": schema}

        payload["params"].update(self._selection(models=models, exclude=exclude))

        if kwargs is not None:
            payload["params"]["task_tags"] = kwargs

        return self._post(data=json.dumps(payload))

    def seed(self, *, show: bool = False, **kwargs) -> requests.Response:
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
        **kwargs
    ) -> requests.Response:
        data = self._default_request(method="docs.generate")
        data["params"] = {"compile": compile}

        data["params"].update(self._selection(models=models, exclude=exclude))

        if kwargs is not None:
            data["params"]["task_tags"] = kwargs

        return self._post(data=json.dumps(data))

    def run_operation(
        self, *, macro: str, args: Optional[Dict[str, Any]] = None, **kwargs
    ) -> requests.Response:
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
        data = self._default_request(method="snapshot-freshness")
        data["params"].update(self._selection(select=select))

        if kwargs is not None:
            data["params"]["task_tags"] = kwargs

        return self._post(data=json.dumps(data))

    def compile_sql(self, *, sql: str, name: str) -> requests.Response:
        data = self._default_request(method="compile_sql")
        data["params"] = {"sql": b64(sql.encode("utf-8")).decode("utf-8"), "name": name}
        return self._post(data=json.dumps(data))

    def run_sql(self, *, sql: str, name: str) -> requests.Response:
        data = self._default_request(method="run_sql")
        data["params"] = {"sql": b64(sql.encode("utf-8")).decode("utf-8"), "name": name}
        return self._post(data=json.dumps(data))


@resource(
    description="A resource representing a dbt rpc client.",
    config_schema={
        "hostname": Field(StringSource, is_required=False, default_value="0.0.0.0"),
        "port": Field(IntSource, is_required=False, default_value=8580),
    },
)
def dbt_rpc_resource(context) -> DbtRpcClient:
    return DbtRpcClient(
        host=context.resource_config["hostname"], port=context.resource_config["port"]
    )
