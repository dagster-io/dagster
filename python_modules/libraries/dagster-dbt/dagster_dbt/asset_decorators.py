from typing import Any, Callable, Optional

from dagster import AssetsDefinition, PartitionsDefinition, multi_asset
from typing_extensions import TypedDict, Unpack

from .asset_utils import get_dbt_multi_asset_args, get_deps
from .cli.resources_v2 import DbtManifest
from .utils import ASSET_RESOURCE_TYPES, select_unique_ids_from_manifest


def _dbt_multi_asset(
    *,
    manifest: DbtManifest,
    select: str = "fqn:*",
    exclude: Optional[str] = None,
) -> Callable[..., AssetsDefinition]:
    """Create a definition for how to compute a set of dbt resources, described by a manifest.json.

    Args:
        manifest (DbtManifest): The wrapper of a dbt manifest.json.
        select (Optional[str]): A dbt selection string for the models in a project that you want
            to include. Defaults to "*".
        exclude (Optional[str]): A dbt selection string for the models in a project that you want
            to exclude. Defaults to "".

    Examples:
        .. code-block:: python

            @dbt_multi_asset(manifest=manifest)
            def my_dbt_assets(dbt: ResourceParam["DbtCliClient"]):
                yield from dbt.cli(["run"])
    """
    unique_ids = select_unique_ids_from_manifest(
        select=select, exclude=exclude or "", manifest_json=manifest.raw_manifest
    )
    deps = get_deps(
        dbt_nodes=manifest.node_info_by_dbt_unique_id,
        selected_unique_ids=unique_ids,
        asset_resource_types=ASSET_RESOURCE_TYPES,
    )
    (
        non_argument_deps,
        outs,
        internal_asset_deps,
    ) = get_dbt_multi_asset_args(
        manifest=manifest,
        deps=deps,
    )

    def inner(fn) -> AssetsDefinition:
        asset_definition = multi_asset(
            outs=outs,
            internal_asset_deps=internal_asset_deps,
            non_argument_deps=non_argument_deps,
            compute_kind="dbt",
            can_subset=True,
            op_tags={
                **({"dagster-dbt/select": select} if select else {}),
                **({"dagster-dbt/exclude": exclude} if exclude else {}),
            },
        )(fn)

        asset_definition = asset_definition.with_attributes(
            output_asset_key_replacements=manifest.output_asset_key_replacements,
        )

        return asset_definition

    return inner


class DbtMultiAssetWithAttributesParams(TypedDict, total=False):
    partition_defs: PartitionsDefinition


class dbt_multi_asset:
    def __init__(
        self,
        *,
        manifest: DbtManifest,
        select: str = "fqn:*",
        exclude: Optional[str] = None,
    ):
        self.manifest = manifest
        self.select = select
        self.exclude = exclude

    def __call__(self, fn: Callable[..., Any]) -> AssetsDefinition:
        assets_definition = _dbt_multi_asset(
            manifest=self.manifest, select=self.select, exclude=self.exclude
        )(fn)

        # Apply any explicit Dagster metadata that the user has supplied.
        # This is useful in the case where the framework cannot infer certain
        # metadata, such as partition definitions.
        assets_definition.with_attributes(**self._with_attributes_kwargs)

        return assets_definition

    def with_attributes(
        self, **kwargs: Unpack[DbtMultiAssetWithAttributesParams]
    ) -> "dbt_multi_asset":
        self._with_attributes_kwargs = kwargs

        return self
