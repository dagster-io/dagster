from typing import Callable, Optional

from dagster import (
    AssetsDefinition,
    AssetSpec,
    multi_asset,
)
from dlt.extract.source import DltSource
from dlt.pipeline.pipeline import Pipeline

from .constants import META_KEY_PIPELINE, META_KEY_SOURCE, META_KEY_TRANSLATOR
from .translator import DagsterDltTranslator


def dlt_assets(
    *,
    dlt_source: DltSource,
    dlt_pipeline: Pipeline,
    name: Optional[str] = None,
    group_name: Optional[str] = None,
    dlt_dagster_translator: DagsterDltTranslator = DagsterDltTranslator(),
) -> Callable[..., AssetsDefinition]:
    def inner(fn) -> AssetsDefinition:
        specs = [
            AssetSpec(
                key=dlt_dagster_translator.get_asset_key(dlt_source_resource),
                deps=dlt_dagster_translator.get_deps_asset_keys(dlt_source_resource),
                auto_materialize_policy=dlt_dagster_translator.get_auto_materialize_policy(
                    dlt_source_resource
                ),
                metadata={  # type: ignore - source / translator are included in metadata for use in `.run()`
                    META_KEY_SOURCE: dlt_source,
                    META_KEY_PIPELINE: dlt_pipeline,
                    META_KEY_TRANSLATOR: dlt_dagster_translator,
                },
            )
            for dlt_source_resource in dlt_source.resources.values()
        ]
        assets_definition = multi_asset(
            specs=specs, name=name, group_name=group_name, compute_kind="dlt", can_subset=True
        )(fn)
        return assets_definition

    return inner
