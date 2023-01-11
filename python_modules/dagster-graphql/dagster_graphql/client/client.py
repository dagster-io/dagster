from itertools import chain
from typing import Any, Dict, Iterable, List, Mapping, Optional

import dagster._check as check
import requests.exceptions
from dagster import DagsterRunStatus
from dagster._annotations import public
from dagster._core.definitions.utils import validate_tags
from dagster._utils.backcompat import experimental_class_warning
from gql import Client, gql
from gql.transport import Transport
from gql.transport.requests import RequestsHTTPTransport

from .client_queries import (
    CLIENT_GET_REPO_LOCATIONS_NAMES_AND_PIPELINES_QUERY,
    CLIENT_SUBMIT_PIPELINE_RUN_MUTATION,
    GET_PIPELINE_RUN_STATUS_QUERY,
    RELOAD_REPOSITORY_LOCATION_MUTATION,
    SHUTDOWN_REPOSITORY_LOCATION_MUTATION,
    TERMINATE_RUN_JOB_MUTATION,
)
from .utils import (
    DagsterGraphQLClientError,
    InvalidOutputErrorInfo,
    PipelineInfo,
    ReloadRepositoryLocationInfo,
    ReloadRepositoryLocationStatus,
    ShutdownRepositoryLocationInfo,
    ShutdownRepositoryLocationStatus,
)


class DagsterGraphQLClient:
    """Official Dagster Python Client for GraphQL.

    Utilizes the gql library to dispatch queries over HTTP to a remote Dagster GraphQL Server

    As of now, all operations on this client are synchronous.

    Intended usage:

    .. code-block:: python

        client = DagsterGraphQLClient("localhost", port_number=3000)
        status = client.get_run_status(**SOME_RUN_ID**)

    Args:
        hostname (str): Hostname for the Dagster GraphQL API, like `localhost` or
            `dagit.dagster.YOUR_ORG_HERE`.
        port_number (Optional[int], optional): Optional port number to connect to on the host.
            Defaults to None.
        transport (Optional[Transport], optional): A custom transport to use to connect to the
            GraphQL API with (e.g. for custom auth). Defaults to None.
        use_https (bool, optional): Whether to use https in the URL connection string for the
            GraphQL API. Defaults to False.

    Raises:
        :py:class:`~requests.exceptions.ConnectionError`: if the client cannot connect to the host.
    """

    def __init__(
        self,
        hostname: str,
        port_number: Optional[int] = None,
        transport: Optional[Transport] = None,
        use_https: bool = False,
    ):
        experimental_class_warning(self.__class__.__name__)

        self._hostname = check.str_param(hostname, "hostname")
        self._port_number = check.opt_int_param(port_number, "port_number")
        self._use_https = check.bool_param(use_https, "use_https")

        self._url = (
            ("https://" if self._use_https else "http://")
            + (f"{self._hostname}:{self._port_number}" if self._port_number else self._hostname)
            + "/graphql"
        )

        self._transport = check.opt_inst_param(
            transport,
            "transport",
            Transport,
            default=RequestsHTTPTransport(url=self._url, use_json=True),
        )
        try:
            self._client = Client(transport=self._transport, fetch_schema_from_transport=True)
        except requests.exceptions.ConnectionError as exc:
            raise DagsterGraphQLClientError(
                f"Error when connecting to url {self._url}. "
                + f"Did you specify hostname: {self._hostname} "
                + (f"and port_number: {self._port_number} " if self._port_number else "")
                + "correctly?"
            ) from exc

    def _execute(self, query: str, variables: Optional[Dict[str, Any]] = None):
        try:
            return self._client.execute(gql(query), variable_values=variables)
        except Exception as exc:  # catch generic Exception from the gql client
            raise DagsterGraphQLClientError(
                f"Exception occured during execution of query \n{query}\n with variables"
                f" \n{variables}\n"
            ) from exc

    def _get_repo_locations_and_names_with_pipeline(self, pipeline_name: str) -> List[PipelineInfo]:
        res_data = self._execute(CLIENT_GET_REPO_LOCATIONS_NAMES_AND_PIPELINES_QUERY)
        query_res = res_data["repositoriesOrError"]
        repo_connection_status = query_res["__typename"]
        if repo_connection_status == "RepositoryConnection":
            valid_nodes: Iterable[PipelineInfo] = chain(
                *map(PipelineInfo.from_node, query_res["nodes"])
            )
            return [info for info in valid_nodes if info.pipeline_name == pipeline_name]
        else:
            raise DagsterGraphQLClientError(repo_connection_status, query_res["message"])

    def _core_submit_execution(
        self,
        pipeline_name: str,
        repository_location_name: Optional[str] = None,
        repository_name: Optional[str] = None,
        run_config: Optional[Mapping[str, Any]] = None,
        mode: Optional[str] = None,
        preset: Optional[str] = None,
        tags: Optional[Dict[str, Any]] = None,
        solid_selection: Optional[List[str]] = None,
        is_using_job_op_graph_apis: Optional[bool] = False,
    ):
        check.opt_str_param(repository_location_name, "repository_location_name")
        check.opt_str_param(repository_name, "repository_name")
        check.str_param(pipeline_name, "pipeline_name")
        check.opt_str_param(mode, "mode")
        check.opt_str_param(preset, "preset")
        run_config = check.opt_mapping_param(run_config, "run_config")

        # The following invariant will never fail when a job is executed
        check.invariant(
            (mode is not None and run_config is not None) or preset is not None,
            (
                "Either a mode and run_config or a preset must be specified in order to "
                f"submit the pipeline {pipeline_name} for execution"
            ),
        )
        tags = validate_tags(tags)

        pipeline_or_job = "Job" if is_using_job_op_graph_apis else "Pipeline"

        if not repository_location_name or not repository_name:
            pipeline_info_lst = self._get_repo_locations_and_names_with_pipeline(pipeline_name)
            if len(pipeline_info_lst) == 0:
                raise DagsterGraphQLClientError(
                    f"{pipeline_or_job}NotFoundError",
                    (
                        f"No {'jobs' if is_using_job_op_graph_apis else 'pipelines'} with the name"
                        f" `{pipeline_name}` exist"
                    ),
                )
            elif len(pipeline_info_lst) == 1:
                pipeline_info = pipeline_info_lst[0]
                repository_location_name = pipeline_info.repository_location_name
                repository_name = pipeline_info.repository_name
            else:
                raise DagsterGraphQLClientError(
                    "Must specify repository_location_name and repository_name since there are"
                    f" multiple {'jobs' if is_using_job_op_graph_apis else 'pipelines'} with the"
                    f" name {pipeline_name}.\n\tchoose one of: {pipeline_info_lst}"
                )

        variables: Dict[str, Any] = {
            "executionParams": {
                "selector": {
                    "repositoryLocationName": repository_location_name,
                    "repositoryName": repository_name,
                    "pipelineName": pipeline_name,
                    "solidSelection": solid_selection,
                }
            }
        }
        if preset is not None:
            variables["executionParams"]["preset"] = preset
        if mode is not None and run_config is not None:
            variables["executionParams"] = {
                **variables["executionParams"],
                "runConfigData": run_config,
                "mode": mode,
                "executionMetadata": {"tags": [{"key": k, "value": v} for k, v in tags.items()]}
                if tags
                else {},
            }

        res_data: Dict[str, Any] = self._execute(CLIENT_SUBMIT_PIPELINE_RUN_MUTATION, variables)
        query_result = res_data["launchPipelineExecution"]
        query_result_type = query_result["__typename"]
        if (
            query_result_type == "LaunchRunSuccess"
            or query_result_type == "LaunchPipelineRunSuccess"
        ):
            return query_result["run"]["runId"]
        elif query_result_type == "InvalidStepError":
            raise DagsterGraphQLClientError(query_result_type, query_result["invalidStepKey"])
        elif query_result_type == "InvalidOutputError":
            error_info = InvalidOutputErrorInfo(
                step_key=query_result["stepKey"],
                invalid_output_name=query_result["invalidOutputName"],
            )
            raise DagsterGraphQLClientError(query_result_type, body=error_info)
        elif (
            query_result_type == "RunConfigValidationInvalid"
            or query_result_type == "PipelineConfigValidationInvalid"
        ):
            raise DagsterGraphQLClientError(query_result_type, query_result["errors"])
        else:
            # query_result_type is a ConflictingExecutionParamsError, a PresetNotFoundError
            # a PipelineNotFoundError, a RunConflict, or a PythonError
            raise DagsterGraphQLClientError(query_result_type, query_result["message"])

    def submit_pipeline_execution(
        self,
        pipeline_name: str,
        repository_location_name: Optional[str] = None,
        repository_name: Optional[str] = None,
        run_config: Optional[Any] = None,
        mode: Optional[str] = None,
        preset: Optional[str] = None,
        tags: Optional[Dict[str, Any]] = None,
        solid_selection: Optional[List[str]] = None,
    ) -> str:
        """Submits a Pipeline with attached configuration for execution.

        Args:
            pipeline_name (str): The pipeline's name
            repository_location_name (Optional[str], optional): The name of the repository location where
                the pipeline is located. If omitted, the client will try to infer the repository location
                from the available options on the Dagster deployment. Defaults to None.
            repository_name (Optional[str], optional): The name of the repository where the pipeline is located.
                If omitted, the client will try to infer the repository from the available options
                on the Dagster deployment. Defaults to None.
            run_config (Optional[Any], optional): This is the run config to execute the pipeline with.
                Note that runConfigData is any-typed in the GraphQL type system. This type is used when passing in
                an arbitrary object for run config. However, it must conform to the constraints of the config
                schema for this pipeline. If it does not, the client will throw a DagsterGraphQLClientError with a message of
                RunConfigValidationInvalid. Defaults to None.
            mode (Optional[str], optional): The mode to run the pipeline with. If you have not
                defined any custom modes for your pipeline, the default mode is "default". Defaults to None.
            preset (Optional[str], optional): The name of a pre-defined preset to use instead of a
                run config. Defaults to None.
            tags (Optional[Dict[str, Any]], optional): A set of tags to add to the pipeline execution.

        Raises:
            DagsterGraphQLClientError("InvalidStepError", invalid_step_key): the pipeline has an invalid step
            DagsterGraphQLClientError("InvalidOutputError", body=error_object): some solid has an invalid output within the pipeline.
                The error_object is of type dagster_graphql.InvalidOutputErrorInfo.
            DagsterGraphQLClientError("ConflictingExecutionParamsError", invalid_step_key): a preset and a run_config & mode are present
                that conflict with one another
            DagsterGraphQLClientError("PresetNotFoundError", message): if the provided preset name is not found
            DagsterGraphQLClientError("RunConflict", message): a `DagsterRunConflict` occured during execution.
                This indicates that a conflicting pipeline run already exists in run storage.
            DagsterGraphQLClientError("PipelineConfigurationInvalid", invalid_step_key): the run_config is not in the expected format
                for the pipeline
            DagsterGraphQLClientError("PipelineNotFoundError", message): the requested pipeline does not exist
            DagsterGraphQLClientError("PythonError", message): an internal framework error occurred

        Returns:
            str: run id of the submitted pipeline run
        """
        return self._core_submit_execution(
            pipeline_name,
            repository_location_name,
            repository_name,
            run_config,
            mode,
            preset,
            tags,
            solid_selection,
            is_using_job_op_graph_apis=False,
        )

    @public
    def submit_job_execution(
        self,
        job_name: str,
        repository_location_name: Optional[str] = None,
        repository_name: Optional[str] = None,
        run_config: Optional[Dict[str, Any]] = None,
        tags: Optional[Dict[str, Any]] = None,
        op_selection: Optional[List[str]] = None,
    ) -> str:
        """Submits a job with attached configuration for execution.

        Args:
            job_name (str): The job's name
            repository_location_name (Optional[str]): The name of the repository location where
                the job is located. If omitted, the client will try to infer the repository location
                from the available options on the Dagster deployment. Defaults to None.
            repository_name (Optional[str]): The name of the repository where the job is located.
                If omitted, the client will try to infer the repository from the available options
                on the Dagster deployment. Defaults to None.
            run_config (Optional[Dict[str, Any]]): This is the run config to execute the job with.
                Note that runConfigData is any-typed in the GraphQL type system. This type is used when passing in
                an arbitrary object for run config. However, it must conform to the constraints of the config
                schema for this job. If it does not, the client will throw a DagsterGraphQLClientError with a message of
                JobConfigValidationInvalid. Defaults to None.
            tags (Optional[Dict[str, Any]]): A set of tags to add to the job execution.

        Raises:
            DagsterGraphQLClientError("InvalidStepError", invalid_step_key): the job has an invalid step
            DagsterGraphQLClientError("InvalidOutputError", body=error_object): some solid has an invalid output within the job.
                The error_object is of type dagster_graphql.InvalidOutputErrorInfo.
            DagsterGraphQLClientError("RunConflict", message): a `DagsterRunConflict` occured during execution.
                This indicates that a conflicting job run already exists in run storage.
            DagsterGraphQLClientError("PipelineConfigurationInvalid", invalid_step_key): the run_config is not in the expected format
                for the job
            DagsterGraphQLClientError("JobNotFoundError", message): the requested job does not exist
            DagsterGraphQLClientError("PythonError", message): an internal framework error occurred

        Returns:
            str: run id of the submitted pipeline run
        """
        return self._core_submit_execution(
            pipeline_name=job_name,
            repository_location_name=repository_location_name,
            repository_name=repository_name,
            run_config=run_config,
            mode="default",
            preset=None,
            tags=tags,
            solid_selection=op_selection,
            is_using_job_op_graph_apis=True,
        )

    @public
    def get_run_status(self, run_id: str) -> DagsterRunStatus:
        """Get the status of a given Pipeline Run.

        Args:
            run_id (str): run id of the requested pipeline run.

        Raises:
            DagsterGraphQLClientError("PipelineNotFoundError", message): if the requested run id is not found
            DagsterGraphQLClientError("PythonError", message): on internal framework errors

        Returns:
            DagsterRunStatus: returns a status Enum describing the state of the requested pipeline run
        """
        check.str_param(run_id, "run_id")

        res_data: Dict[str, Dict[str, Any]] = self._execute(
            GET_PIPELINE_RUN_STATUS_QUERY, {"runId": run_id}
        )
        query_result: Dict[str, Any] = res_data["pipelineRunOrError"]
        query_result_type: str = query_result["__typename"]
        if query_result_type == "PipelineRun" or query_result_type == "Run":
            return DagsterRunStatus(query_result["status"])
        else:
            raise DagsterGraphQLClientError(query_result_type, query_result["message"])

    @public
    def reload_repository_location(
        self, repository_location_name: str
    ) -> ReloadRepositoryLocationInfo:
        """Reloads a Dagster Repository Location, which reloads all repositories in that repository location.

        This is useful in a variety of contexts, including refreshing Dagit without restarting
        the server.

        Args:
            repository_location_name (str): The name of the repository location

        Returns:
            ReloadRepositoryLocationInfo: Object with information about the result of the reload request
        """
        check.str_param(repository_location_name, "repository_location_name")

        res_data: Dict[str, Dict[str, Any]] = self._execute(
            RELOAD_REPOSITORY_LOCATION_MUTATION,
            {"repositoryLocationName": repository_location_name},
        )

        query_result: Dict[str, Any] = res_data["reloadRepositoryLocation"]
        query_result_type: str = query_result["__typename"]
        if query_result_type == "WorkspaceLocationEntry":
            location_or_error_type = query_result["locationOrLoadError"]["__typename"]
            if location_or_error_type == "RepositoryLocation":
                return ReloadRepositoryLocationInfo(status=ReloadRepositoryLocationStatus.SUCCESS)
            else:
                return ReloadRepositoryLocationInfo(
                    status=ReloadRepositoryLocationStatus.FAILURE,
                    failure_type="PythonError",
                    message=query_result["locationOrLoadError"]["message"],
                )
        else:
            # query_result_type is either ReloadNotSupported or RepositoryLocationNotFound
            return ReloadRepositoryLocationInfo(
                status=ReloadRepositoryLocationStatus.FAILURE,
                failure_type=query_result_type,
                message=query_result["message"],
            )

    @public
    def shutdown_repository_location(
        self, repository_location_name: str
    ) -> ShutdownRepositoryLocationInfo:
        """Shuts down the server that is serving metadata for the provided repository location.

        This is primarily useful when you want the server to be restarted by the compute environment
        in which it is running (for example, in Kubernetes, the pod in which the server is running
        will automatically restart when the server is shut down, and the repository metadata will
        be reloaded)

        Args:
            repository_location_name (str): The name of the repository location

        Returns:
            ShutdownRepositoryLocationInfo: Object with information about the result of the reload request
        """
        check.str_param(repository_location_name, "repository_location_name")

        res_data: Dict[str, Dict[str, Any]] = self._execute(
            SHUTDOWN_REPOSITORY_LOCATION_MUTATION,
            {"repositoryLocationName": repository_location_name},
        )

        query_result: Dict[str, Any] = res_data["shutdownRepositoryLocation"]
        query_result_type: str = query_result["__typename"]
        if query_result_type == "ShutdownRepositoryLocationSuccess":
            return ShutdownRepositoryLocationInfo(status=ShutdownRepositoryLocationStatus.SUCCESS)
        elif (
            query_result_type == "RepositoryLocationNotFound" or query_result_type == "PythonError"
        ):
            return ShutdownRepositoryLocationInfo(
                status=ShutdownRepositoryLocationStatus.FAILURE,
                message=query_result["message"],
            )
        else:
            raise Exception(f"Unexpected query result type {query_result_type}")

    def terminate_run(self, run_id: str):
        """
        Terminates a pipeline run. This method it is useful when you would like to stop a pipeline run
        based on a external event.

        Args:
            run_id (str): The run id of the pipeline run to terminate
        """
        check.str_param(run_id, "run_id")

        res_data: Dict[str, Dict[str, Any]] = self._execute(
            TERMINATE_RUN_JOB_MUTATION, {"runId": run_id}
        )

        query_result: Dict[str, Any] = res_data["terminateRun"]
        query_result_type: str = query_result["__typename"]
        if query_result_type == "TerminateRunSuccess":
            return

        elif query_result_type == "RunNotFoundError":
            raise DagsterGraphQLClientError("RunNotFoundError", f"Run Id {run_id} not found")
        else:
            raise DagsterGraphQLClientError(query_result_type, query_result["message"])
