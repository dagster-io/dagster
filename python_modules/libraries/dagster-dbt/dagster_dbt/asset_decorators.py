from functools import wraps
from typing import (
    Any,
    Callable,
    Generator,
    Iterator,
    Mapping,
    NamedTuple,
    Optional,
    TypeVar,
    Union,
    cast,
    overload,
)
from dagster import (
    op,
    AssetsDefinition,
    OpExecutionContext,
    ConfigurableResource,
    AssetObservation,
    Output,
    Out,
    asset,
    materialize_to_memory,
)
from typing_extensions import ParamSpec
import dagster._check as check
from dagster._core.decorator_utils import get_function_params
from dagster._core.definitions.decorators.op_decorator import is_context_provided
from dagster._core.definitions.op_definition import OpDefinition
from dagster._core.definitions.partition import PartitionsDefinition
from dagster._core.execution.context.invocation import build_op_context
from torch import ExcludeDispatchKeyGuard


class DbtExecutionContext(OpExecutionContext):
    def __init__(
        self,
        op_context: OpExecutionContext,
        manifest_path: str,
        base_select: str,
        base_exclude: Optional[str],
    ):
        super().__init__(op_context._step_execution_context)
        self.manifest_path = manifest_path
        self.base_select = base_select
        self.base_exclude = base_exclude

    @property
    def all_selected(self) -> bool:
        return self.selected_output_names == len(self.op_def.output_defs)

    @property
    def dbt_select(self) -> str:
        return self.base_select if self.all_selected else "fqn stuff"

    @property
    def dbt_exclude(self) -> Optional[str]:
        return self.base_exclude if self.all_selected else None


class DbtAssetResource(ConfigurableResource):
    project_dir: str
    profiles_dir: str
    json_log_format: bool = True

    def _event_iterator(self, command: str, **kwargs):
        pass

    def cli(self, command: str, **kwargs):
        pass

    def run(
        self, context: DbtExecutionContext, **kwargs
    ) -> Iterator[Union[AssetObservation, Output]]:
        yield from self._event_iterator(
            "run", select=context.dbt_select, exclude=context.dbt_exclude, **kwargs
        )


def dbt_assets(
    *,
    manifest_path: str,
    select: Optional[str] = None,
    exclude: Optional[str] = None,
    partitions_def: Optional[PartitionsDefinition] = None,
    op_name: Optional[str] = None,
    node_info_to_asset_properties_fn: Optional[
        Callable[[Mapping[str, Any]], Mapping[str, Any]]
    ] = None,
) -> Callable[..., AssetsDefinition]:
    def inner(fn) -> AssetsDefinition:
        @op(
            name=op_name,
            tags={"kind": "dbt"},
            out={"a": Out(), "b": Out()},
        )
        @wraps(fn)
        def _op(*args, **kwargs):
            if is_context_provided(get_function_params(fn)):
                # convert the OpExecutionContext into a DbtExecutionContext, which has
                # additional context related to dbt
                return fn(
                    DbtExecutionContext(cast(OpExecutionContext, args[0]), manifest_path),
                    *args[1:],
                    **kwargs,
                )
            else:
                return fn(*args, **kwargs)

        return AssetsDefinition(
            node_def=_op,
        )

    return inner


@dbt_assets(manifest_path="manifest.json")
def dbt_run_assets(
    context: DbtExecutionContext, dbt: DbtAssetResource
):  # , dbt: DbtAssetResource):
    print("hi")
    print(dbt.project_dir)
    assert isinstance(context, DbtExecutionContext)
    assert isinstance(context, OpExecutionContext)
    return 1, 2


print(dbt_run_assets)

materialize_to_memory(
    [dbt_run_assets],
    resources={
        "dbt": DbtAssetResource(project_dir="foo", profiles_dir="bar", json_log_format=True)
    },
)
