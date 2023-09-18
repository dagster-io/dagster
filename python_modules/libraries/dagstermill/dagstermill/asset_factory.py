import pickle
import tempfile
from typing import Any, Callable, Iterable, Mapping, Optional, Set, Type, Union, cast

import dagster._check as check
from dagster import (
    AssetIn,
    AssetKey,
    AssetsDefinition,
    Failure,
    Output,
    PartitionsDefinition,
    ResourceDefinition,
    RetryPolicy,
    RetryRequested,
    SourceAsset,
    asset,
)
from dagster._config.pythonic_config import Config, infer_schema_from_config_class
from dagster._config.pythonic_config.inheritance_utils import safe_is_subclass
from dagster._core.definitions.events import CoercibleToAssetKey, CoercibleToAssetKeyPrefix
from dagster._core.definitions.utils import validate_tags
from dagster._core.execution.context.compute import OpExecutionContext

from dagstermill.factory import _clean_path_for_windows, execute_notebook


def _make_dagstermill_asset_compute_fn(
    name: str,
    notebook_path: str,
    save_notebook_on_failure: bool,
) -> Callable:
    def _t_fn(context: OpExecutionContext, **inputs) -> Iterable:
        check.param_invariant(
            isinstance(context.run_config, dict),
            "context",
            "StepExecutionContext must have valid run_config",
        )

        with tempfile.TemporaryDirectory() as output_notebook_dir:
            executed_notebook_path = execute_notebook(
                context.get_step_execution_context(),
                name=name,
                inputs=inputs,
                save_notebook_on_failure=save_notebook_on_failure,
                notebook_path=notebook_path,
                output_notebook_dir=output_notebook_dir,
            )

            with open(executed_notebook_path, "rb") as fd:
                yield Output(fd.read())

            # deferred import for perf
            import scrapbook

            output_nb = scrapbook.read_notebook(executed_notebook_path)

            for key, value in output_nb.scraps.items():
                if key.startswith("event-"):
                    with open(value.data, "rb") as fd:
                        event = pickle.loads(fd.read())
                        if isinstance(event, (Failure, RetryRequested)):
                            raise event
                        else:
                            yield event

    return _t_fn


def define_dagstermill_asset(
    name: str,
    notebook_path: str,
    key_prefix: Optional[CoercibleToAssetKeyPrefix] = None,
    ins: Optional[Mapping[str, AssetIn]] = None,
    deps: Optional[Iterable[Union[CoercibleToAssetKey, AssetsDefinition, SourceAsset]]] = None,
    metadata: Optional[Mapping[str, Any]] = None,
    config_schema: Optional[Union[Any, Mapping[str, Any]]] = None,
    required_resource_keys: Optional[Set[str]] = None,
    resource_defs: Optional[Mapping[str, ResourceDefinition]] = None,
    description: Optional[str] = None,
    partitions_def: Optional[PartitionsDefinition] = None,
    op_tags: Optional[Mapping[str, Any]] = None,
    group_name: Optional[str] = None,
    io_manager_key: Optional[str] = None,
    retry_policy: Optional[RetryPolicy] = None,
    save_notebook_on_failure: bool = False,
    non_argument_deps: Optional[Union[Set[AssetKey], Set[str]]] = None,
) -> AssetsDefinition:
    """Creates a Dagster asset for a Jupyter notebook.

    Arguments:
        name (str): The name for the asset
        notebook_path (str): Path to the backing notebook
        key_prefix (Optional[Union[str, Sequence[str]]]): If provided, the asset's key is the
            concatenation of the key_prefix and the asset's name, which defaults to the name of
            the decorated function. Each item in key_prefix must be a valid name in dagster (ie only
            contains letters, numbers, and _) and may not contain python reserved keywords.
        ins (Optional[Mapping[str, AssetIn]]): A dictionary that maps input names to information
            about the input.
        deps (Optional[Sequence[Union[AssetsDefinition, SourceAsset, AssetKey, str]]]): The assets
            that are upstream dependencies, but do not pass an input value to the notebook.
        config_schema (Optional[ConfigSchema): The configuration schema for the asset's underlying
            op. If set, Dagster will check that config provided for the op matches this schema and fail
            if it does not. If not set, Dagster will accept any config provided for the op.
        metadata (Optional[Dict[str, Any]]): A dict of metadata entries for the asset.
        required_resource_keys (Optional[Set[str]]): Set of resource handles required by the notebook.
        description (Optional[str]): Description of the asset to display in the Dagster UI.
        partitions_def (Optional[PartitionsDefinition]): Defines the set of partition keys that
            compose the asset.
        op_tags (Optional[Dict[str, Any]]): A dictionary of tags for the op that computes the asset.
            Frameworks may expect and require certain metadata to be attached to a op. Values that
            are not strings will be json encoded and must meet the criteria that
            `json.loads(json.dumps(value)) == value`.
        group_name (Optional[str]): A string name used to organize multiple assets into groups. If not provided,
            the name "default" is used.
        resource_defs (Optional[Mapping[str, ResourceDefinition]]):
            (Experimental) A mapping of resource keys to resource definitions. These resources
            will be initialized during execution, and can be accessed from the
            context within the notebook.
        io_manager_key (Optional[str]): A string key for the IO manager used to store the output notebook.
            If not provided, the default key output_notebook_io_manager will be used.
        retry_policy (Optional[RetryPolicy]): The retry policy for the op that computes the asset.
        save_notebook_on_failure (bool): If True and the notebook fails during execution, the failed notebook will be
            written to the Dagster storage directory. The location of the file will be printed in the Dagster logs.
            Defaults to False.
        non_argument_deps (Optional[Union[Set[AssetKey], Set[str]]]): Deprecated, use deps instead. Set of asset keys that are
            upstream dependencies, but do not pass an input to the asset.

    Examples:
        .. code-block:: python

            from dagstermill import define_dagstermill_asset
            from dagster import asset, AssetIn, AssetKey
            from sklearn import datasets
            import pandas as pd
            import numpy as np

            @asset
            def iris_dataset():
                sk_iris = datasets.load_iris()
                return pd.DataFrame(
                    data=np.c_[sk_iris["data"], sk_iris["target"]],
                    columns=sk_iris["feature_names"] + ["target"],
                )

            iris_kmeans_notebook = define_dagstermill_asset(
                name="iris_kmeans_notebook",
                notebook_path="/path/to/iris_kmeans.ipynb",
                ins={
                    "iris": AssetIn(key=AssetKey("iris_dataset"))
                }
            )
    """
    check.str_param(name, "name")
    check.str_param(notebook_path, "notebook_path")
    check.bool_param(save_notebook_on_failure, "save_notebook_on_failure")

    required_resource_keys = set(
        check.opt_set_param(required_resource_keys, "required_resource_keys", of_type=str)
    )
    ins = check.opt_mapping_param(ins, "ins", key_type=str, value_type=AssetIn)

    if isinstance(key_prefix, str):
        key_prefix = [key_prefix]

    key_prefix = check.opt_list_param(key_prefix, "key_prefix", of_type=str)

    default_description = f"This asset is backed by the notebook at {notebook_path}"
    description = check.opt_str_param(description, "description", default=default_description)

    io_mgr_key = check.opt_str_param(
        io_manager_key, "io_manager_key", default="output_notebook_io_manager"
    )

    user_tags = validate_tags(op_tags)
    if op_tags is not None:
        check.invariant(
            "notebook_path" not in op_tags,
            "user-defined op tags contains the `notebook_path` key, but the `notebook_path` key"
            " is reserved for use by Dagster",
        )
        check.invariant(
            "kind" not in op_tags,
            "user-defined op tags contains the `kind` key, but the `kind` key is reserved for"
            " use by Dagster",
        )

    default_tags = {"notebook_path": _clean_path_for_windows(notebook_path), "kind": "ipynb"}

    if safe_is_subclass(config_schema, Config):
        config_schema = infer_schema_from_config_class(cast(Type[Config], config_schema))

    return asset(
        name=name,
        key_prefix=key_prefix,
        ins=ins,
        deps=deps,
        metadata=metadata,
        description=description,
        config_schema=config_schema,
        required_resource_keys=required_resource_keys,
        resource_defs=resource_defs,
        partitions_def=partitions_def,
        op_tags={**user_tags, **default_tags},
        group_name=group_name,
        output_required=False,
        io_manager_key=io_mgr_key,
        retry_policy=retry_policy,
        non_argument_deps=non_argument_deps,
    )(
        _make_dagstermill_asset_compute_fn(
            name=name,
            notebook_path=notebook_path,
            save_notebook_on_failure=save_notebook_on_failure,
        )
    )
