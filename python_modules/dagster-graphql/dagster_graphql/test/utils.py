import asyncio
from contextlib import contextmanager
from typing import Any, Dict, Iterator, Mapping, Optional, Sequence

import dagster._check as check
from dagster._core.host_representation.external import ExternalRepository
from dagster._core.instance import DagsterInstance
from dagster._core.test_utils import wait_for_runs_to_finish
from dagster._core.workspace.context import WorkspaceProcessContext, WorkspaceRequestContext
from dagster._core.workspace.load_target import PythonFileTarget
from typing_extensions import Protocol, TypeAlias, TypedDict

from dagster_graphql.schema import create_schema


class GqlResult(Protocol):
    @property
    def data(self) -> Mapping[str, Any]:
        ...

    @property
    def errors(self) -> Optional[Sequence[str]]:
        ...


Selector: TypeAlias = Dict[str, Any]

GqlVariables: TypeAlias = Mapping[str, Any]


class GqlTag(TypedDict):
    key: str
    value: str


class GqlAssetKey(TypedDict):
    path: Sequence[str]


def main_repo_location_name() -> str:
    return "test_location"


def main_repo_name() -> str:
    return "test_repo"


SCHEMA = create_schema()


def execute_dagster_graphql(
    context: WorkspaceRequestContext, query: str, variables: Optional[GqlVariables] = None
) -> GqlResult:
    result = SCHEMA.execute(
        query,
        context_value=context,
        variable_values=variables,
    )

    if result.errors:
        first_error = result.errors[0]
        if hasattr(first_error, "original_error") and first_error.original_error:
            raise result.errors[0].original_error

        raise result.errors[0]

    return result


def execute_dagster_graphql_subscription(
    context: WorkspaceRequestContext,
    query: str,
    variables: Optional[GqlVariables] = None,
) -> Sequence[GqlResult]:
    results = []

    subscription = SCHEMA.subscribe(
        query,
        context_value=context,
        variable_values=variables,
    )

    async def _process():
        payload_aiter = await subscription
        async for res in payload_aiter:
            results.append(res)
            # first payload should have it all
            break

    asyncio.run(_process())

    return results


def execute_dagster_graphql_and_finish_runs(
    context: WorkspaceRequestContext, query: str, variables: Optional[GqlVariables] = None
) -> GqlResult:
    result = execute_dagster_graphql(context, query, variables)
    wait_for_runs_to_finish(context.instance, timeout=30)
    return result


@contextmanager
def define_out_of_process_context(
    python_file: str, fn_name: str, instance: DagsterInstance, read_only: bool = False
) -> Iterator[WorkspaceRequestContext]:
    check.inst_param(instance, "instance", DagsterInstance)

    with define_out_of_process_workspace(
        python_file, fn_name, instance, read_only=read_only
    ) as workspace_process_context:
        yield workspace_process_context.create_request_context()


def define_out_of_process_workspace(
    python_file: str, fn_name: str, instance: DagsterInstance, read_only: bool = False
) -> WorkspaceProcessContext:
    return WorkspaceProcessContext(
        instance,
        PythonFileTarget(
            python_file=python_file,
            attribute=fn_name,
            working_directory=None,
            location_name=main_repo_location_name(),
        ),
        version="",
        read_only=read_only,
    )


def infer_repository(graphql_context: WorkspaceRequestContext) -> ExternalRepository:
    if len(graphql_context.code_locations) == 1:
        # This is to account for having a single in process repository
        code_location = graphql_context.code_locations[0]
        repositories = code_location.get_repositories()
        assert len(repositories) == 1
        return next(iter(repositories.values()))

    code_location = graphql_context.get_code_location("test")
    return code_location.get_repository("test_repo")


def infer_repository_selector(graphql_context: WorkspaceRequestContext) -> Selector:
    if len(graphql_context.code_locations) == 1:
        # This is to account for having a single in process repository
        code_location = graphql_context.code_locations[0]
        repositories = code_location.get_repositories()
        assert len(repositories) == 1
        repository = next(iter(repositories.values()))
    else:
        code_location = graphql_context.get_code_location("test")
        repository = code_location.get_repository("test_repo")

    return {
        "repositoryLocationName": code_location.name,
        "repositoryName": repository.name,
    }


def infer_job_or_pipeline_selector(
    graphql_context: WorkspaceRequestContext,
    pipeline_name: str,
    solid_selection: Optional[Sequence[str]] = None,
    asset_selection: Optional[Sequence[GqlAssetKey]] = None,
) -> Selector:
    selector = infer_repository_selector(graphql_context)
    selector.update(
        {
            "pipelineName": pipeline_name,
            "solidSelection": solid_selection,
            "assetSelection": asset_selection,
        }
    )
    return selector


def infer_pipeline_selector(
    graphql_context: WorkspaceRequestContext,
    pipeline_name: str,
    solid_selection: Optional[Sequence[str]] = None,
) -> Selector:
    selector = infer_repository_selector(graphql_context)
    selector.update(
        {
            "pipelineName": pipeline_name,
            "solidSelection": solid_selection,
        }
    )
    return selector


def infer_schedule_selector(
    graphql_context: WorkspaceRequestContext, schedule_name: str
) -> Selector:
    selector = infer_repository_selector(graphql_context)
    selector.update({"scheduleName": schedule_name})
    return selector


def infer_sensor_selector(graphql_context: WorkspaceRequestContext, sensor_name: str) -> Selector:
    selector = infer_repository_selector(graphql_context)
    selector.update({"sensorName": sensor_name})
    return selector


def infer_instigation_selector(graphql_context: WorkspaceRequestContext, name: str) -> Selector:
    selector = infer_repository_selector(graphql_context)
    selector.update({"name": name})
    return selector


def infer_resource_selector(graphql_context: WorkspaceRequestContext, name: str) -> Selector:
    selector = infer_repository_selector(graphql_context)
    selector = {**selector, **{"resourceName": name}}
    return selector
