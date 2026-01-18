import functools
import sys
from asyncio import iscoroutinefunction
from collections.abc import Awaitable, Callable, Iterable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime
from types import TracebackType
from typing import (
    TYPE_CHECKING,
    Any,
    NamedTuple,
    Optional,
    TypeAlias,
    TypeVar,
    Union,
    cast,
    overload,
)

import dagster._check as check
from dagster._core.asset_graph_view.asset_graph_view import AssetGraphView
from dagster._core.definitions.asset_checks.asset_check_spec import AssetCheckKey
from dagster._core.definitions.assets.graph.base_asset_graph import EntityKey
from dagster._core.definitions.assets.graph.remote_asset_graph import (
    RemoteAssetCheckNode,
    RemoteAssetNode,
    RemoteWorkspaceAssetGraph,
)
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.partitions.definition import PartitionsDefinition
from dagster._core.definitions.selector import (
    GraphSelector,
    JobSelector,
    JobSubsetSelector,
    RepositorySelector,
    ScheduleSelector,
    SensorSelector,
)
from dagster._core.definitions.temporal_context import TemporalContext
from dagster._core.errors import DagsterError, DagsterInvariantViolationError
from dagster._core.execution.backfill import PartitionBackfill
from dagster._core.remote_representation.code_location import is_implicit_asset_job_name
from dagster._core.remote_representation.external import RemoteJob, RemoteSchedule, RemoteSensor
from dagster._core.storage.dagster_run import DagsterRun
from dagster._core.workspace.context import RemoteDefinition
from dagster._core.workspace.permissions import Permissions
from dagster._utils.caching_instance_queryer import CachingInstanceQueryer
from dagster._utils.error import serializable_error_info_from_exc_info
from typing_extensions import ParamSpec

if TYPE_CHECKING:
    from dagster._core.workspace.context import BaseWorkspaceRequestContext

    from dagster_graphql.schema.errors import GrapheneError, GraphenePythonError
    from dagster_graphql.schema.util import ResolveInfo

P = ParamSpec("P")
T = TypeVar("T")

GrapheneResolverFn: TypeAlias = Callable[..., object]
T_Callable = TypeVar("T_Callable", bound=Callable)


def assert_permission_for_location(
    graphene_info: "ResolveInfo", permission: str, location_name: str
) -> None:
    from dagster_graphql.schema.errors import GrapheneUnauthorizedError

    context = cast("BaseWorkspaceRequestContext", graphene_info.context)
    if not context.has_permission_for_location(permission, location_name):
        raise UserFacingGraphQLError(GrapheneUnauthorizedError())


def require_permission_check(
    permission: str,
):
    def decorator(fn):
        if iscoroutinefunction(fn):

            @functools.wraps(fn)
            async def _async_fn(self, graphene_info, *args: P.args, **kwargs: P.kwargs):
                result = await fn(self, graphene_info, *args, **kwargs)
                if not graphene_info.context.was_permission_checked(permission):
                    raise Exception(f"Permission {permission} was never checked during the request")
                return result

            return _async_fn
        else:

            @functools.wraps(fn)
            def _fn(self, graphene_info, *args: P.args, **kwargs: P.kwargs):
                result = fn(self, graphene_info, *args, **kwargs)

                if not graphene_info.context.was_permission_checked(permission):
                    raise Exception(f"Permission {permission} was never checked during the request")

                return result

            return _fn

    return decorator


def check_permission(
    permission: str,
):
    def decorator(fn):
        if iscoroutinefunction(fn):

            @functools.wraps(fn)
            async def _async_fn(self, graphene_info, *args: P.args, **kwargs: P.kwargs):
                assert_permission(graphene_info, permission)

                return await fn(self, graphene_info, *args, **kwargs)

            return _async_fn
        else:

            @functools.wraps(fn)
            def _fn(self, graphene_info, *args: P.args, **kwargs: P.kwargs):
                assert_permission(graphene_info, permission)

                return fn(self, graphene_info, *args, **kwargs)

            return _fn

    return decorator


def assert_permission(graphene_info: "ResolveInfo", permission: str) -> None:
    from dagster_graphql.schema.errors import GrapheneUnauthorizedError

    context = cast("BaseWorkspaceRequestContext", graphene_info.context)
    if not context.has_permission(permission):
        raise UserFacingGraphQLError(GrapheneUnauthorizedError())


def has_permission_for_asset_graph(
    graphene_info: "ResolveInfo",
    asset_graph: RemoteWorkspaceAssetGraph,
    entity_keys: Optional[Sequence[EntityKey]],
    permission: str,
) -> bool:
    all_keys = set(entity_keys) if entity_keys else set()
    context = cast("BaseWorkspaceRequestContext", graphene_info.context)

    # if we have the permission for the whole deployment, no need to check specific asset keys or locations
    if context.has_permission(permission):
        return True

    if (
        not any(
            context.has_permission_for_location(permission, location_name)
            for location_name in context.code_location_names
        )
        and not context.viewer_has_any_owner_definition_permissions()
    ):
        # short-circuit if we don't have any location-level permissions or definition-level permissions
        return False

    location_names = set()
    if all_keys:
        for key in all_keys:
            if not asset_graph.has(key):
                # If any of the asset keys don't map to a location (e.g. because they are no longer in the
                # graph) need deployment-wide permissions - no valid code location to check
                return context.has_permission(permission)
            location_name = asset_graph.get_repository_handle(key).location_name
            location_names.add(location_name)
    else:
        location_names = set(
            handle.location_name for handle in asset_graph.repository_handles_by_key.values()
        )

    if not location_names:
        return context.has_permission(permission)

    # if we have permission for all locations relevant to the asset graph, we're good
    if all(
        context.has_permission_for_location(permission, location_name)
        for location_name in location_names
    ):
        return True

    # No need to check individual asset keys if we don't have owner permissions
    if not context.viewer_has_any_owner_definition_permissions():
        return False

    if not all_keys:
        return False

    return all(
        context.has_permission_for_selector(permission, entity_key) for entity_key in all_keys
    )


def assert_permission_for_asset_graph(
    graphene_info: "ResolveInfo",
    asset_graph: RemoteWorkspaceAssetGraph,
    entity_keys: Optional[Sequence[EntityKey]],
    permission: str,
) -> None:
    from dagster_graphql.schema.errors import GrapheneUnauthorizedError

    if not has_permission_for_asset_graph(graphene_info, asset_graph, entity_keys, permission):
        raise UserFacingGraphQLError(GrapheneUnauthorizedError())


def has_permission_for_definition(
    graphene_info: "ResolveInfo", permission: str, remote_definition: RemoteDefinition
):
    if graphene_info.context.has_permission(permission):
        return True

    location_name = location_name_for_remote_definition(remote_definition)
    if graphene_info.context.has_permission_for_location(permission, location_name):
        return True

    if not graphene_info.context.viewer_has_any_owner_definition_permissions():
        return False

    if isinstance(remote_definition, RemoteAssetCheckNode):
        owners = graphene_info.context.get_owners_for_selector(remote_definition.asset_check.key)
    else:
        owners = remote_definition.owners

    if not owners:
        return False

    return graphene_info.context.has_permission_for_owners(permission, owners)


def location_name_for_remote_definition(remote_definition: RemoteDefinition) -> str:
    if isinstance(remote_definition, RemoteAssetNode):
        return (
            remote_definition.resolve_to_singular_repo_scoped_node().repository_handle.location_name
        )
    elif isinstance(
        remote_definition,
        (RemoteJob, RemoteSchedule, RemoteSensor, RemoteAssetCheckNode),
    ):
        return remote_definition.handle.location_name
    else:
        check.failed(f"Unexpected remote definition type {type(remote_definition)}")


def has_permission_for_run(
    graphene_info: "ResolveInfo", permission: Permissions, run: DagsterRun
) -> bool:
    if not run.remote_job_origin:
        return graphene_info.context.has_permission(permission)

    return has_permission_for_job(
        graphene_info,
        permission,
        JobSelector(
            location_name=run.remote_job_origin.location_name,
            repository_name=run.remote_job_origin.repository_origin.repository_name,
            job_name=run.job_name,
        ),
        entity_keys=list(run.entity_selection) if run.entity_selection else None,
    )


def assert_permission_for_run(
    graphene_info: "ResolveInfo", permission: Permissions, run: DagsterRun
) -> None:
    from dagster_graphql.schema.errors import GrapheneUnauthorizedError

    if not has_permission_for_run(graphene_info, permission, run):
        raise UserFacingGraphQLError(GrapheneUnauthorizedError())


def has_permission_for_job(
    graphene_info: "ResolveInfo",
    permission: Permissions,
    job_selector: JobSelector,
    entity_keys: Optional[
        Sequence[EntityKey]
    ] = None,  # entity keys are only required for implicit asset jobs
) -> bool:
    if is_implicit_asset_job_name(job_selector.job_name):
        return has_permission_for_asset_graph(
            graphene_info, graphene_info.context.asset_graph, entity_keys, permission
        )

    return graphene_info.context.has_permission_for_selector(permission, job_selector)


def assert_permission_for_job(
    graphene_info: "ResolveInfo",
    permission: Permissions,
    job_selector: JobSelector,
    entity_keys: Optional[
        Sequence[EntityKey]
    ] = None,  # entity keys are only required for implicit asset jobs
):
    from dagster_graphql.schema.errors import GrapheneUnauthorizedError

    if not has_permission_for_job(graphene_info, permission, job_selector, entity_keys):
        raise UserFacingGraphQLError(GrapheneUnauthorizedError())


def assert_permission_for_sensor(
    graphene_info: "ResolveInfo",
    permission: Permissions,
    sensor_selector: SensorSelector,
):
    from dagster_graphql.schema.errors import GrapheneUnauthorizedError

    if not graphene_info.context.has_permission_for_selector(permission, sensor_selector):
        raise UserFacingGraphQLError(GrapheneUnauthorizedError())


def assert_permission_for_schedule(
    graphene_info: "ResolveInfo",
    permission: Permissions,
    schedule_selector: ScheduleSelector,
):
    from dagster_graphql.schema.errors import GrapheneUnauthorizedError

    if not graphene_info.context.has_permission_for_selector(permission, schedule_selector):
        raise UserFacingGraphQLError(GrapheneUnauthorizedError())


def assert_valid_job_partition_backfill(
    graphene_info: "ResolveInfo",
    backfill: PartitionBackfill,
    partitions_def: PartitionsDefinition,
    dynamic_partitions_store: CachingInstanceQueryer,
    backfill_datetime: datetime,
) -> None:
    from dagster_graphql.schema.errors import GraphenePartitionKeysNotFoundError

    partition_names = backfill.get_partition_names(graphene_info.context)

    if not partition_names:
        return

    invalid_keys = set(partition_names) - set(
        partitions_def.get_partition_keys(backfill_datetime, dynamic_partitions_store)
    )

    if invalid_keys:
        raise UserFacingGraphQLError(GraphenePartitionKeysNotFoundError(invalid_keys))


def has_permission_for_backfill(
    graphene_info: "ResolveInfo",
    permission: Permissions,
    backfill: PartitionBackfill,
) -> bool:
    if backfill.is_asset_backfill:
        check.invariant(
            backfill.asset_selection is not None, "Asset backfill must have asset selection"
        )
        return has_permission_for_asset_graph(
            graphene_info,
            graphene_info.context.asset_graph,
            cast("list[AssetKey]", backfill.asset_selection),
            permission,
        )

    # job backfill, check permissions for the job
    if not backfill.partition_set_origin:
        return graphene_info.context.has_permission(permission)

    partition_selector = backfill.partition_set_origin.selector
    if not graphene_info.context.has_code_location_name(partition_selector.location_name):
        return graphene_info.context.has_permission(permission)

    partition_sets = graphene_info.context.get_partition_sets(
        repository_selector=RepositorySelector(
            location_name=partition_selector.location_name,
            repository_name=partition_selector.repository_name,
        )
    )
    matches = [
        partition_set
        for partition_set in partition_sets
        if partition_set.name == partition_selector.partition_set_name
    ]

    if len(matches) != 1:
        return graphene_info.context.has_permission_for_location(
            permission, partition_selector.location_name
        )

    remote_partition_set = next(iter(matches))
    return graphene_info.context.has_permission_for_selector(
        permission,
        JobSelector(
            location_name=partition_selector.location_name,
            repository_name=partition_selector.repository_name,
            job_name=remote_partition_set.job_name,
        ),
    )


def assert_permission_for_backfill(
    graphene_info: "ResolveInfo",
    permission: Permissions,
    backfill: PartitionBackfill,
) -> None:
    from dagster_graphql.schema.errors import GrapheneUnauthorizedError

    if not has_permission_for_backfill(graphene_info, permission, backfill):
        raise UserFacingGraphQLError(GrapheneUnauthorizedError())


def assert_valid_asset_partition_backfill(
    graphene_info: "ResolveInfo",
    backfill: PartitionBackfill,
    backfill_datetime: datetime,
) -> None:
    from dagster_graphql.schema.errors import GraphenePartitionKeysNotFoundError

    asset_graph = graphene_info.context.asset_graph
    asset_backfill_data = backfill.asset_backfill_data

    asset_graph_view = AssetGraphView(
        temporal_context=TemporalContext(
            effective_dt=backfill_datetime,
            last_event_id=None,
        ),
        instance=graphene_info.context.instance,
        asset_graph=asset_graph,
    )

    if not asset_backfill_data:
        return

    checked_execution_set_asset_keys = set()

    for asset_key in asset_backfill_data.target_subset.asset_keys:
        asset_node = asset_graph.get(asset_key)

        entity_subset = asset_graph_view.get_entity_subset_from_asset_graph_subset(
            asset_backfill_data.target_subset, asset_key
        )

        if asset_key not in checked_execution_set_asset_keys:
            checked_execution_set_asset_keys.add(asset_key)
            for execution_set_key in asset_node.execution_set_asset_keys:
                if execution_set_key == asset_key:
                    continue

                if execution_set_key not in asset_backfill_data.target_subset.asset_keys:
                    raise DagsterInvariantViolationError(
                        f"Backfill must include every key in a non-subsettable multi-asset, included "
                        f"{asset_key.to_user_string()} but not {execution_set_key.to_user_string()}"
                    )

                other_entity_subset = asset_graph_view.get_entity_subset_from_asset_graph_subset(
                    asset_backfill_data.target_subset, execution_set_key
                )

                if entity_subset.get_internal_value() != other_entity_subset.get_internal_value():
                    raise DagsterInvariantViolationError(
                        f"Targeted subset must match between every key in"
                        f" a non-subsettable multi-asset, but does not match between {asset_key.to_user_string()} "
                        f"and {execution_set_key.to_user_string()}"
                    )

                checked_execution_set_asset_keys.add(execution_set_key)

        partitions_def = asset_node.partitions_def

        if not partitions_def:
            continue

        invalid_subset = asset_graph_view.get_subset_not_in_graph(
            key=asset_key, candidate_subset=entity_subset
        )

        if not invalid_subset.is_empty:
            raise UserFacingGraphQLError(
                GraphenePartitionKeysNotFoundError(
                    set(invalid_subset.expensively_compute_partition_keys())
                )
            )

        for parent_key in asset_graph.get(asset_key).parent_keys:
            _parent_subset, required_but_nonexistent_subset = (
                asset_graph_view.compute_parent_subset_and_required_but_nonexistent_subset(
                    parent_key,
                    entity_subset,
                )
            )

            if not required_but_nonexistent_subset.is_empty:
                raise DagsterInvariantViolationError(
                    f"Targeted partition subset {entity_subset}"
                    f" depends on non-existent partitions: {required_but_nonexistent_subset}"
                )


def _noop(_) -> None:
    pass


class ErrorCapture:
    @staticmethod
    def default_on_exception(
        exc_info: tuple[type[BaseException], BaseException, TracebackType],
    ) -> "GraphenePythonError":
        from dagster_graphql.schema.errors import GraphenePythonError

        # Transform exception in to PythonError to present to user
        return GraphenePythonError(serializable_error_info_from_exc_info(exc_info))

    # global behavior for how to handle unexpected exceptions
    on_exception = default_on_exception

    # context var for observing unexpected exceptions
    observer: ContextVar[Callable[[Exception], None]] = ContextVar(
        "error_capture_observer", default=_noop
    )

    @staticmethod
    @contextmanager
    def watch(fn: Callable[[Exception], None]) -> Iterator[None]:
        token = ErrorCapture.observer.set(fn)
        try:
            yield
        finally:
            ErrorCapture.observer.reset(token)


@overload
def capture_error(
    fn: Callable[P, T],
) -> Callable[P, T]: ...


@overload
def capture_error(  # pyright: ignore[reportOverlappingOverload]
    fn: Callable[P, Awaitable[T]],
) -> Callable[P, Awaitable[T]]: ...


def capture_error(
    fn: Union[Callable[P, T], Callable[P, Awaitable[T]]],
) -> Union[
    Callable[P, Union[T, "GrapheneError", "GraphenePythonError"]],
    Callable[P, Awaitable[Union[T, "GrapheneError", "GraphenePythonError"]]],
]:
    if iscoroutinefunction(fn):

        @functools.wraps(fn)
        async def _async_fn(*args: P.args, **kwargs: P.kwargs) -> T:
            try:
                return await fn(*args, **kwargs)
            except UserFacingGraphQLError as de_exception:
                return de_exception.error
            except Exception as exc:
                ErrorCapture.observer.get()(exc)
                return ErrorCapture.on_exception(sys.exc_info())  # type: ignore

        return _async_fn

    else:

        @functools.wraps(fn)
        def _fn(*args: P.args, **kwargs: P.kwargs) -> T:
            try:
                return cast("T", fn(*args, **kwargs))
            except UserFacingGraphQLError as de_exception:
                return de_exception.error
            except Exception as exc:
                ErrorCapture.observer.get()(exc)
                return ErrorCapture.on_exception(sys.exc_info())  # type: ignore

        return _fn


class UserFacingGraphQLError(Exception):
    # The `error` arg here should be a Graphene type implementing the interface `GrapheneError`, but
    # this is not trackable by the Python type system.
    def __init__(self, error: Any):
        self.error = error
        message = "[{cls}] {message}".format(
            cls=error.__class__.__name__,
            message=error.message if hasattr(error, "message") else None,
        )
        super().__init__(message)


def pipeline_selector_from_graphql(data: Mapping[str, Any]) -> JobSubsetSelector:
    asset_selection = cast("Optional[Iterable[dict[str, list[str]]]]", data.get("assetSelection"))
    asset_check_selection = cast(
        "Optional[Iterable[dict[str, Any]]]", data.get("assetCheckSelection")
    )
    return JobSubsetSelector(
        location_name=data["repositoryLocationName"],
        repository_name=data["repositoryName"],
        job_name=data.get("pipelineName") or data.get("jobName"),  # type: ignore
        op_selection=data.get("solidSelection"),
        asset_selection=(
            [AssetKey.from_graphql_input(asset_key) for asset_key in asset_selection]
            if asset_selection
            else None
        ),
        asset_check_selection=(
            [AssetCheckKey.from_graphql_input(asset_check) for asset_check in asset_check_selection]
            if asset_check_selection is not None
            else None
        ),
    )


def graph_selector_from_graphql(data: Mapping[str, Any]) -> GraphSelector:
    return GraphSelector(
        location_name=data["repositoryLocationName"],
        repository_name=data["repositoryName"],
        graph_name=data["graphName"],
    )


class ExecutionParams(
    NamedTuple(
        "_ExecutionParams",
        [
            ("selector", JobSubsetSelector),
            ("run_config", Mapping[str, object]),
            ("mode", Optional[str]),
            ("execution_metadata", "ExecutionMetadata"),
            ("step_keys", Optional[Sequence[str]]),
        ],
    )
):
    def __new__(
        cls,
        selector: JobSubsetSelector,
        run_config: Optional[Mapping[str, object]],
        mode: Optional[str],
        execution_metadata: "ExecutionMetadata",
        step_keys: Optional[Sequence[str]],
    ):
        check.opt_list_param(step_keys, "step_keys", of_type=str)

        return super().__new__(
            cls,
            selector=check.inst_param(selector, "selector", JobSubsetSelector),
            run_config=check.opt_mapping_param(run_config, "run_config", key_type=str),
            mode=check.opt_str_param(mode, "mode"),
            execution_metadata=check.inst_param(
                execution_metadata, "execution_metadata", ExecutionMetadata
            ),
            step_keys=step_keys,
        )

    def to_graphql_input(self) -> Mapping[str, Any]:
        return {
            "selector": self.selector.to_graphql_input(),
            "runConfigData": self.run_config,
            "mode": self.mode,
            "executionMetadata": self.execution_metadata.to_graphql_input(),
            "stepKeys": self.step_keys,
        }


class ExecutionMetadata(
    NamedTuple(
        "_ExecutionMetadata",
        [
            ("run_id", Optional[str]),
            ("tags", Mapping[str, str]),
            ("root_run_id", Optional[str]),
            ("parent_run_id", Optional[str]),
        ],
    )
):
    def __new__(
        cls,
        run_id: Optional[str],
        tags: Mapping[str, str],
        root_run_id: Optional[str] = None,
        parent_run_id: Optional[str] = None,
    ):
        return super().__new__(
            cls,
            check.opt_str_param(run_id, "run_id"),
            check.dict_param(tags, "tags", key_type=str, value_type=str),
            check.opt_str_param(root_run_id, "root_run_id"),
            check.opt_str_param(parent_run_id, "parent_run_id"),
        )

    def to_graphql_input(self) -> Mapping[str, Any]:
        return {
            "runId": self.run_id,
            "tags": [{"key": k, "value": v} for k, v in self.tags.items()],
            "rootRunId": self.root_run_id,
            "parentRunId": self.parent_run_id,
        }


def apply_cursor_limit_reverse(
    items: Sequence[str],
    cursor: Optional[str],
    limit: Optional[int],
    reverse: Optional[bool],
) -> Sequence[str]:
    start = 0
    end = len(items)
    index = 0

    if cursor:
        index = next(idx for (idx, item) in enumerate(items) if item == cursor)

        if reverse:
            end = index
        else:
            start = index + 1

    if limit:
        if reverse:
            start = end - limit
        else:
            end = start + limit

    return items[max(start, 0) : end]


def get_query_limit_with_default(provided_limit: Optional[int], default_limit: int) -> int:
    check.opt_int_param(provided_limit, "provided_limit")

    if provided_limit is None:
        return default_limit

    if provided_limit > default_limit:
        raise DagsterError(f"Limit of {provided_limit} is too large. Max is {default_limit}")

    return provided_limit


BackfillParams: TypeAlias = Mapping[str, Any]
AssetBackfillPreviewParams: TypeAlias = Mapping[str, Any]
