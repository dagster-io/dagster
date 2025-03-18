import asyncio
import sys
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Optional, Union, cast

import dagster._check as check
import graphene
from dagster._core.definitions.asset_job import IMPLICIT_ASSET_JOB_NAME
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.instance import DagsterInstance
from dagster._core.remote_representation.external import RemoteRepository
from dagster._core.test_utils import wait_for_runs_to_finish
from dagster._core.workspace.context import WorkspaceProcessContext, WorkspaceRequestContext
from dagster._core.workspace.load_target import PythonFileTarget
from typing_extensions import Protocol, TypeAlias, TypedDict

from dagster_graphql import __file__ as dagster_graphql_init_py
from dagster_graphql.schema import create_schema


class GqlResult(Protocol):
    @property
    def data(self) -> Mapping[str, Any]: ...

    @property
    def errors(self) -> Optional[Sequence[str]]: ...


Selector: TypeAlias = dict[str, Any]

GqlVariables: TypeAlias = Mapping[str, Any]


class GqlTag(TypedDict):
    key: str
    value: str


class GqlAssetKey(TypedDict):
    path: Sequence[str]


class GqlAssetCheckHandle(TypedDict):
    assetKey: GqlAssetKey
    name: str


def main_repo_location_name() -> str:
    return "test_location"


def main_repo_name() -> str:
    return "test_repo"


SCHEMA = create_schema()


def execute_dagster_graphql(
    context: WorkspaceRequestContext,
    query: str,
    variables: Optional[GqlVariables] = None,
    schema: graphene.Schema = SCHEMA,
) -> GqlResult:
    result = asyncio.run(
        schema.execute_async(
            query,
            context_value=context,
            variable_values=variables,
        )
    )
    # It would be cleaner if we instead passed in a process context
    # and made a request context for this invocation.
    # For now just ensure we don't shared loaders between requests.
    context.loaders.clear()

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
    schema: graphene.Schema = SCHEMA,
) -> Sequence[GqlResult]:
    results = []

    subscription = schema.subscribe(
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
    python_file: str,
    fn_name: Optional[str],
    instance: DagsterInstance,
    read_only: bool = False,
    read_only_locations: Optional[Mapping[str, bool]] = None,
) -> Iterator[WorkspaceRequestContext]:
    check.inst_param(instance, "instance", DagsterInstance)

    with define_out_of_process_workspace(
        python_file, fn_name, instance, read_only=read_only
    ) as workspace_process_context:
        yield WorkspaceRequestContext(
            instance=instance,
            current_workspace=workspace_process_context.get_current_workspace(),
            process_context=workspace_process_context,
            version=workspace_process_context.version,
            source=None,
            read_only=read_only,
            read_only_locations=read_only_locations,
        )


def define_out_of_process_workspace(
    python_file: str, fn_name: Optional[str], instance: DagsterInstance, read_only: bool = False
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


def infer_repository(graphql_context: WorkspaceRequestContext) -> RemoteRepository:
    if len(graphql_context.code_locations) == 1:
        # This is to account for having a single in process repository
        code_location = graphql_context.code_locations[0]
        repositories = code_location.get_repositories()
        assert len(repositories) == 1
        return next(iter(repositories.values()))

    code_location = graphql_context.get_code_location(main_repo_location_name())
    return code_location.get_repository("test_repo")


def infer_repository_selector(graphql_context: WorkspaceRequestContext) -> Selector:
    if len(graphql_context.code_locations) == 1:
        # This is to account for having a single in process repository
        code_location = graphql_context.code_locations[0]
        repositories = code_location.get_repositories()
        assert len(repositories) == 1
        repository = next(iter(repositories.values()))
    else:
        code_location = graphql_context.get_code_location(main_repo_location_name())
        repository = code_location.get_repository("test_repo")

    return {
        "repositoryLocationName": code_location.name,
        "repositoryName": repository.name,
    }


def infer_job_selector(
    graphql_context: WorkspaceRequestContext,
    job_name: str,
    op_selection: Optional[Sequence[str]] = None,
    asset_selection: Optional[Sequence[GqlAssetKey]] = None,
    asset_check_selection: Optional[Sequence[GqlAssetCheckHandle]] = None,
) -> Selector:
    selector = infer_repository_selector(graphql_context)
    selector.update(
        {
            "pipelineName": job_name,
            "solidSelection": op_selection,
            "assetSelection": asset_selection,
            "assetCheckSelection": asset_check_selection,
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


def ensure_dagster_graphql_tests_import() -> None:
    dagster_package_root = (Path(dagster_graphql_init_py) / ".." / "..").resolve()
    assert (
        dagster_package_root / "dagster_graphql_tests"
    ).exists(), "Could not find dagster_graphql_tests where expected"
    sys.path.append(dagster_package_root.as_posix())


def materialize_assets(
    context: WorkspaceRequestContext,
    asset_selection: Optional[Sequence[AssetKey]] = None,
    partition_keys: Optional[Sequence[str]] = None,
    run_config_data: Optional[Mapping[str, Any]] = None,
) -> Union[GqlResult, Sequence[GqlResult]]:
    from dagster_graphql.client.query import LAUNCH_PIPELINE_EXECUTION_MUTATION

    gql_asset_selection = (
        cast(Sequence[GqlAssetKey], [key.to_graphql_input() for key in asset_selection])
        if asset_selection
        else None
    )
    selector = infer_job_selector(
        context, IMPLICIT_ASSET_JOB_NAME, asset_selection=gql_asset_selection
    )
    if partition_keys:
        results = []
        for key in partition_keys:
            results.append(
                execute_dagster_graphql(
                    context,
                    LAUNCH_PIPELINE_EXECUTION_MUTATION,
                    variables={
                        "executionParams": {
                            "selector": selector,
                            "executionMetadata": {
                                "tags": [{"key": "dagster/partition", "value": key}]
                            },
                            "runConfigData": run_config_data,
                        }
                    },
                )
            )
        return results
    else:
        selector = infer_job_selector(
            context, IMPLICIT_ASSET_JOB_NAME, asset_selection=gql_asset_selection
        )
        return execute_dagster_graphql(
            context,
            LAUNCH_PIPELINE_EXECUTION_MUTATION,
            variables={
                "executionParams": {
                    "selector": selector,
                    "runConfigData": run_config_data,
                }
            },
        )
