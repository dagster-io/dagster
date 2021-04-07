from typing import Any, Dict, Optional

from dagster import check
from dagster.core.storage.pipeline_run import PipelineRunStatus
from dagster.utils.backcompat import experimental_class_warning
from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport

from .client_queries import GET_PIPELINE_RUN_STATUS_QUERY, RELOAD_REPOSITORY_LOCATION_MUTATION
from .utils import (
    DagsterGraphQLClientError,
    ReloadRepositoryLocationInfo,
    ReloadRepositoryLocationStatus,
)


class DagsterGraphQLClient:
    """Official Dagster Python Client for GraphQL

    Utilizes the gql library to dispatch queries over HTTP to a remote Dagster GraphQL Server

    As of now, all operations on this client are synchronous.

    Intended usage:

    .. code-block:: python

        client = DagsterGraphQLClient("localhost", port_number=3000)
        status = client.get_run_status(**SOME_RUN_ID**)

    """

    def __init__(self, hostname: str, port_number: Optional[int] = None):
        experimental_class_warning(self.__class__.__name__)
        self._hostname = check.str_param(hostname, "hostname")
        self._port_number = check.opt_int_param(port_number, "port_number")
        self._url = (
            "http://"
            + (f"{self._hostname}:{self._port_number}" if self._port_number else self._hostname)
            + "/graphql"
        )
        self._transport = RequestsHTTPTransport(url=self._url, use_json=True)
        self._client = Client(transport=self._transport, fetch_schema_from_transport=True)

    def _execute(self, query: str, variables: Dict[str, Any]):
        try:
            return self._client.execute(gql(query), variable_values=variables)
        except Exception as exc:  # catch generic Exception from the gql client
            raise DagsterGraphQLClientError(
                f"Query \n{query}\n with variables \n{variables}\n failed GraphQL validation"
            ) from exc

    def submit_pipeline_execution(
        self,
        pipeline_name: str,
        repository_location_name: Optional[str] = None,
        repository_name: Optional[str] = None,
        run_config: Optional[Any] = None,
        mode: Optional[str] = None,
        preset: Optional[str] = None,
    ) -> str:
        raise NotImplementedError("not yet implemented")

    def get_run_status(self, run_id: str) -> PipelineRunStatus:
        """Get the status of a given Pipeline Run

        Args:
            run_id (str): run id of the requested pipeline run.

        Raises:
            DagsterGraphQLClientError("PipelineNotFoundError", message): if the requested run id is not found
            DagsterGraphQLClientError("PythonError", message): on internal framework errors

        Returns:
            PipelineRunStatus: returns a status Enum describing the state of the requested pipeline run
        """
        check.str_param(run_id, "run_id")

        res_data: Dict[str, Dict[str, Any]] = self._execute(
            GET_PIPELINE_RUN_STATUS_QUERY, {"runId": run_id}
        )
        query_result: Dict[str, Any] = res_data["pipelineRunOrError"]
        query_result_type: str = query_result["__typename"]
        if query_result_type == "PipelineRun":
            return query_result["status"]
        else:
            raise DagsterGraphQLClientError(query_result_type, query_result["message"])

    def reload_repository_location(
        self, repository_location_name: str
    ) -> ReloadRepositoryLocationInfo:
        """Reloads a Dagster Repository Location, which reloads all repositories in that repository location.

            This is useful in a variety of contexts, including refreshing Dagit without restarting
            the server.

        Args:
            repository_location_name (str): The name of the repository location

        Returns:
            ReloadRepositoryLocationInfo: Object with a `.status` attribute of `ReloadRepositoryLocationStatus.SUCCESS` if successful.
              Otherwise, returns an object with a `.status` attribute of `ReloadRepositoryLocationStatus.FAILURE`
              if the reload failed, and a `.message` attribute with the attached error message
        """
        check.str_param(repository_location_name, "repository_location_name")

        res_data: Dict[str, Dict[str, Any]] = self._execute(
            RELOAD_REPOSITORY_LOCATION_MUTATION,
            {"repositoryLocationName": repository_location_name},
        )
        query_result: Dict[str, Any] = res_data["reloadRepositoryLocation"]
        query_result_type: str = query_result["__typename"]
        if query_result_type == "RepositoryLocation":
            return ReloadRepositoryLocationInfo(status=ReloadRepositoryLocationStatus.SUCCESS)
        else:
            return ReloadRepositoryLocationInfo(
                status=ReloadRepositoryLocationStatus.FAILURE,
                message=query_result["error"]["message"],
            )
