import logging
import re
import time
from collections.abc import Callable, Mapping
from contextlib import contextmanager
from email.utils import mktime_tz, parsedate_tz
from typing import Any, Optional

import requests
from dagster_shared import check
from requests.adapters import HTTPAdapter
from requests.exceptions import (
    ChunkedEncodingError,
    ConnectionError as RequestsConnectionError,
    HTTPError,
    ReadTimeout as RequestsReadTimeout,
)

from dagster_cloud_cli.core.errors import (
    DagsterCloudAgentServerError,
    DagsterCloudHTTPError,
    DagsterCloudMaintenanceException,
)
from dagster_cloud_cli.core.headers.auth import DagsterCloudInstanceScope
from dagster_cloud_cli.core.headers.impl import get_dagster_cloud_api_headers

DEFAULT_RETRIES = 6
DEFAULT_BACKOFF_FACTOR = 0.5
DEFAULT_TIMEOUT = 60

logger = logging.getLogger("dagster_cloud")


RETRY_STATUS_CODES = [
    502,
    503,
    504,
    429,
    409,
]


class DagsterCloudAgentHttpClient:
    def __init__(
        self,
        session: requests.Session,
        headers: Optional[dict[str, Any]] = None,
        verify: bool = True,
        timeout: int = DEFAULT_TIMEOUT,
        cookies: Optional[dict[str, Any]] = None,
        proxies: Optional[dict[str, Any]] = None,
        max_retries: int = 0,
        backoff_factor: float = DEFAULT_BACKOFF_FACTOR,
    ):
        self.headers = headers or {}
        self.verify = verify
        self.timeout = timeout
        self.cookies = cookies
        self._session = session
        self._proxies = proxies
        self._max_retries = max_retries
        self._backoff_factor = backoff_factor

    @property
    def session(self) -> requests.Session:
        return self._session

    def post(self, *args, **kwargs):
        return self.execute("POST", *args, **kwargs)

    def get(self, *args, **kwargs):
        return self.execute("GET", *args, **kwargs)

    def put(self, *args, **kwargs):
        return self.execute("PUT", *args, **kwargs)

    def execute(
        self,
        method: str,
        url: str,
        headers: Optional[Mapping[str, str]] = None,
        idempotent: bool = False,
        **kwargs,
    ):
        retry_on_read_timeout = idempotent or bool(
            headers.get("Idempotency-Key") if headers else False
        )

        return _retry_loop(
            lambda: self._execute_retry(method, url, headers, **kwargs),
            max_retries=self._max_retries,
            backoff_factor=self._backoff_factor,
            retry_on_read_timeout=retry_on_read_timeout,
        )

    def _execute_retry(
        self,
        method: str,
        url: str,
        headers: Optional[Mapping[str, Any]],
        **kwargs,
    ):
        response = self._session.request(
            method,
            url,
            headers={
                **(self.headers if self.headers is not None else {}),
                **(headers if headers is not None else {}),
            },
            cookies=self.cookies,
            timeout=self.timeout,
            verify=self.verify,
            proxies=self._proxies,
            **kwargs,
        )
        try:
            result = response.json()
            if not isinstance(result, dict):
                result = {}
        except ValueError:
            result = {}

        if "maintenance" in result:
            maintenance_info = result["maintenance"]
            raise DagsterCloudMaintenanceException(
                message=maintenance_info.get("message"),
                timeout=maintenance_info.get("timeout"),
                retry_interval=maintenance_info.get("retry_interval"),
            )

        if "errors" in result:
            raise DagsterCloudAgentServerError(f"Error in GraphQL response: {result['errors']}")

        response.raise_for_status()

        return result


def _retry_loop(
    execute_retry: Callable,
    max_retries: int,
    backoff_factor: float,
    retry_on_read_timeout: bool,
):
    start_time = time.time()
    retry_number = 0
    error_msg_set = set()
    requested_sleep_time = None
    while True:
        try:
            return execute_retry()
        except (HTTPError, RequestsConnectionError, RequestsReadTimeout, ChunkedEncodingError) as e:
            retryable_error = False
            if isinstance(e, HTTPError):
                retryable_error = e.response.status_code in RETRY_STATUS_CODES
                error_msg = e.response.status_code
                requested_sleep_time = _get_retry_after_sleep_time(e.response.headers)
            elif isinstance(e, RequestsConnectionError):
                retryable_error = True
                error_msg = str(e)
            else:
                retryable_error = retry_on_read_timeout
                error_msg = str(e)

            error_msg_set.add(error_msg)
            if retryable_error and retry_number < max_retries:
                retry_number += 1
                sleep_time = 0
                if requested_sleep_time:
                    sleep_time = requested_sleep_time
                else:
                    sleep_time = backoff_factor * (2**retry_number)

                logger.warning(
                    f"Error in Dagster Cloud request ({error_msg}). Retrying in"
                    f" {sleep_time} seconds..."
                )
                time.sleep(sleep_time)
            else:
                # Throw the error straight if no retries were involved
                if max_retries == 0 or not retryable_error:
                    if isinstance(e, HTTPError):
                        raise DagsterCloudHTTPError(e) from e
                    else:
                        raise
                else:
                    if len(error_msg_set) == 1:
                        status_code_msg = str(next(iter(error_msg_set)))
                    else:
                        status_code_msg = str(error_msg_set)
                    raise DagsterCloudAgentServerError(
                        f"Max retries ({max_retries}) exceeded, too many"
                        f" {status_code_msg} error responses."
                    ) from e
        except DagsterCloudMaintenanceException as e:
            if time.time() - start_time > e.timeout:
                raise

            logger.warning(
                "Dagster Cloud is currently unavailable due to scheduled maintenance. Retrying"
                f" in {e.retry_interval} seconds..."
            )
            time.sleep(e.retry_interval)
        except DagsterCloudAgentServerError:
            raise
        except Exception as e:
            raise DagsterCloudAgentServerError(str(e)) from e


class DagsterCloudGraphQLClient:
    def __init__(
        self,
        url: str,
        session: requests.Session,
        headers: Optional[dict[str, Any]] = None,
        verify: bool = True,
        timeout: int = DEFAULT_TIMEOUT,
        cookies: Optional[dict[str, Any]] = None,
        proxies: Optional[dict[str, Any]] = None,
        max_retries: int = 0,
        backoff_factor: float = DEFAULT_BACKOFF_FACTOR,
    ):
        self.url = url
        self.headers = headers
        self.verify = verify
        self.timeout = timeout
        self.cookies = cookies
        self._session = session
        self._proxies = proxies
        self._max_retries = max_retries
        self._backoff_factor = backoff_factor

    @property
    def session(self) -> requests.Session:
        return self._session

    def execute(
        self,
        query: str,
        variable_values: Optional[Mapping[str, Any]] = None,
        headers: Optional[Mapping[str, str]] = None,
        idempotent_mutation: bool = False,
    ):
        if "mutation " in query and not idempotent_mutation:
            all_headers = {
                **(self.headers if self.headers is not None else {}),
                **(headers if headers is not None else {}),
            }

            # mutations can be made idempotent if they use Idempotency-Key header
            retry_on_read_timeout = bool(all_headers.get("Idempotency-Key"))
        else:
            retry_on_read_timeout = True

        return _retry_loop(
            lambda: self._execute_retry(query, variable_values, headers),
            max_retries=self._max_retries,
            backoff_factor=self._backoff_factor,
            retry_on_read_timeout=retry_on_read_timeout,
        )

    def _execute_retry(
        self,
        query: str,
        variable_values: Optional[Mapping[str, Any]],
        headers: Optional[Mapping[str, Any]],
    ):
        response = self._session.post(
            self.url,
            headers={
                **(self.headers if self.headers is not None else {}),
                **(headers if headers is not None else {}),
                "Content-type": "application/json",
            },
            cookies=self.cookies,
            timeout=self.timeout,
            verify=self.verify,
            json={
                "query": query,
                "variables": variable_values if variable_values else {},
            },
            proxies=self._proxies,
        )
        try:
            result = response.json()
            if not isinstance(result, dict):
                result = {}
        except ValueError:
            result = {}

        if "errors" not in result and "data" not in result and "maintenance" not in result:
            response.raise_for_status()
            raise requests.HTTPError("Unexpected GraphQL response", response=response)

        if "maintenance" in result:
            maintenance_info = result["maintenance"]
            raise DagsterCloudMaintenanceException(
                message=maintenance_info.get("message"),
                timeout=maintenance_info.get("timeout"),
                retry_interval=maintenance_info.get("retry_interval"),
            )

        if "errors" in result:
            raise DagsterCloudAgentServerError(f"Error in GraphQL response: {result['errors']}")

        return result


def get_agent_headers(config_value: dict[str, Any], scope: DagsterCloudInstanceScope):
    return get_dagster_cloud_api_headers(
        config_value["agent_token"],
        scope=scope,
        deployment_name=config_value.get("deployment"),
        additional_headers=config_value.get("headers"),
    )


class HTTPAdapterWithSocketOptions(HTTPAdapter):
    def __init__(self, *args, **kwargs):
        self.socket_options = kwargs.pop("socket_options", None)
        super().__init__(*args, **kwargs)

    def init_poolmanager(self, *args, **kwargs):
        if self.socket_options is not None:
            kwargs["socket_options"] = self.socket_options
        super().init_poolmanager(*args, **kwargs)


@contextmanager
def create_graphql_requests_session(adapter_kwargs: Optional[Mapping[str, Any]] = None):
    with requests.Session() as session:
        adapter = HTTPAdapterWithSocketOptions(**(adapter_kwargs or {}))
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        yield session


def create_agent_http_client(
    session: requests.Session,
    config_value: dict[str, Any],
    scope: DagsterCloudInstanceScope = DagsterCloudInstanceScope.DEPLOYMENT,
):
    return DagsterCloudAgentHttpClient(
        headers=get_agent_headers(config_value, scope=scope),
        verify=config_value.get("verify", True),
        timeout=config_value.get("timeout", DEFAULT_TIMEOUT),
        cookies=config_value.get("cookies", {}),
        # Requests library modifies proxies dictionary so create a copy
        proxies=(
            check.is_dict(config_value.get("proxies")).copy() if config_value.get("proxies") else {}
        ),
        session=session,
        max_retries=config_value.get("retries", DEFAULT_RETRIES),
        backoff_factor=config_value.get("backoff_factor", DEFAULT_BACKOFF_FACTOR),
    )


def create_agent_graphql_client(
    session: requests.Session,
    url: str,
    config_value: dict[str, Any],
    scope: DagsterCloudInstanceScope = DagsterCloudInstanceScope.DEPLOYMENT,
):
    return DagsterCloudGraphQLClient(
        url=url,
        headers=get_agent_headers(config_value, scope=scope),
        verify=config_value.get("verify", True),
        timeout=config_value.get("timeout", DEFAULT_TIMEOUT),
        cookies=config_value.get("cookies", {}),
        # Requests library modifies proxies dictionary so create a copy
        proxies=(
            check.is_dict(config_value.get("proxies")).copy() if config_value.get("proxies") else {}
        ),
        session=session,
        max_retries=config_value.get("retries", DEFAULT_RETRIES),
        backoff_factor=config_value.get("backoff_factor", DEFAULT_BACKOFF_FACTOR),
    )


def _get_retry_after_sleep_time(headers):
    # https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Retry-After

    retry_after = headers.get("Retry-After")
    if retry_after is None:
        return None

    if re.match(r"^\s*[0-9]+\s*$", retry_after):
        seconds = int(retry_after)
    else:
        retry_date = parsedate_tz(retry_after)
        if retry_date is None:
            return None
        retry_date = mktime_tz(retry_date)
        seconds = retry_date - time.time()

    return max(seconds, 0)


@contextmanager
def create_cloud_webserver_client(
    url: str,
    api_token: str,
    retries=3,
    deployment_name: Optional[str] = None,
    headers: Optional[dict[str, Any]] = None,
):
    with create_graphql_requests_session(adapter_kwargs={}) as session:
        yield DagsterCloudGraphQLClient(
            session=session,
            url=f"{url}/graphql",
            headers={
                **get_dagster_cloud_api_headers(
                    api_token,
                    scope=DagsterCloudInstanceScope.DEPLOYMENT,
                    deployment_name=deployment_name,
                ),
                **(headers if headers else {}),
            },
            max_retries=retries,
        )
