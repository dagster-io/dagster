import functools
import sys
from collections.abc import Iterable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime
from types import TracebackType
from typing import TYPE_CHECKING, Any, Callable, NamedTuple, Optional, TypeVar, Union, cast

import dagster._check as check
from dagster._core.definitions.asset_check_spec import AssetCheckKey
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.partition import PartitionsDefinition
from dagster._core.definitions.remote_asset_graph import RemoteWorkspaceAssetGraph
from dagster._core.definitions.selector import GraphSelector, JobSubsetSelector
from dagster._core.execution.backfill import PartitionBackfill
from dagster._core.workspace.context import BaseWorkspaceRequestContext
from dagster._utils.caching_instance_queryer import CachingInstanceQueryer
from dagster._utils.error import serializable_error_info_from_exc_info
from typing_extensions import ParamSpec, TypeAlias

if TYPE_CHECKING:
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

    context = cast(BaseWorkspaceRequestContext, graphene_info.context)
    if not context.has_permission_for_location(permission, location_name):
        raise UserFacingGraphQLError(GrapheneUnauthorizedError())


def require_permission_check(
    permission: str,
) -> Callable[[GrapheneResolverFn], GrapheneResolverFn]:
    def decorator(fn: GrapheneResolverFn) -> GrapheneResolverFn:
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
) -> Callable[[GrapheneResolverFn], GrapheneResolverFn]:
    def decorator(fn: GrapheneResolverFn) -> GrapheneResolverFn:
        @functools.wraps(fn)
        def _fn(self, graphene_info, *args: P.args, **kwargs: P.kwargs):
            assert_permission(graphene_info, permission)

            return fn(self, graphene_info, *args, **kwargs)

        return _fn

    return decorator


def assert_permission(graphene_info: "ResolveInfo", permission: str) -> None:
    from dagster_graphql.schema.errors import GrapheneUnauthorizedError

    context = cast(BaseWorkspaceRequestContext, graphene_info.context)
    if not context.has_permission(permission):
        raise UserFacingGraphQLError(GrapheneUnauthorizedError())


def has_permission_for_asset_graph(
    graphene_info: "ResolveInfo",
    asset_graph: RemoteWorkspaceAssetGraph,
    asset_selection: Optional[Sequence[AssetKey]],
    permission: str,
) -> bool:
    asset_keys = set(asset_selection or [])
    context = cast(BaseWorkspaceRequestContext, graphene_info.context)

    if asset_keys:
        location_names = set()
        for key in asset_keys:
            if not asset_graph.has(key):
                # If any of the asset keys don't map to a location (e.g. because they are no longer in the
                # graph) need deployment-wide permissions - no valid code location to check
                return context.has_permission(permission)
            node = asset_graph.get(key)
            location_names.add(
                node.resolve_to_singular_repo_scoped_node().repository_handle.location_name
            )
    else:
        location_names = set(
            handle.location_name for handle in asset_graph.repository_handles_by_key.values()
        )

    if not location_names:
        return context.has_permission(permission)
    else:
        return all(
            context.has_permission_for_location(permission, location_name)
            for location_name in location_names
        )


def assert_permission_for_asset_graph(
    graphene_info: "ResolveInfo",
    asset_graph: RemoteWorkspaceAssetGraph,
    asset_selection: Optional[Sequence[AssetKey]],
    permission: str,
) -> None:
    from dagster_graphql.schema.errors import GrapheneUnauthorizedError

    if not has_permission_for_asset_graph(graphene_info, asset_graph, asset_selection, permission):
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


def assert_valid_asset_partition_backfill(
    graphene_info: "ResolveInfo",
    backfill: PartitionBackfill,
    dynamic_partitions_store: CachingInstanceQueryer,
    backfill_datetime: datetime,
) -> None:
    from dagster_graphql.schema.errors import GraphenePartitionKeysNotFoundError

    asset_graph = graphene_info.context.asset_graph
    asset_backfill_data = backfill.asset_backfill_data

    if not asset_backfill_data:
        return

    partition_subset_by_asset_key = (
        asset_backfill_data.target_subset.partitions_subsets_by_asset_key
    )

    for asset_key, partition_subset in partition_subset_by_asset_key.items():
        partitions_def = asset_graph.get(asset_key).partitions_def

        if not partitions_def:
            continue

        invalid_keys = set(partition_subset.get_partition_keys()) - set(
            partitions_def.get_partition_keys(backfill_datetime, dynamic_partitions_store)
        )

        if invalid_keys:
            raise UserFacingGraphQLError(GraphenePartitionKeysNotFoundError(invalid_keys))


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


def capture_error(
    fn: Callable[P, T],
) -> Callable[P, Union[T, "GrapheneError", "GraphenePythonError"]]:
    @functools.wraps(fn)
    def _fn(*args: P.args, **kwargs: P.kwargs) -> T:
        try:
            return fn(*args, **kwargs)
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
    asset_selection = cast(Optional[Iterable[dict[str, list[str]]]], data.get("assetSelection"))
    asset_check_selection = cast(
        Optional[Iterable[dict[str, Any]]], data.get("assetCheckSelection")
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


BackfillParams: TypeAlias = Mapping[str, Any]
AssetBackfillPreviewParams: TypeAlias = Mapping[str, Any]
