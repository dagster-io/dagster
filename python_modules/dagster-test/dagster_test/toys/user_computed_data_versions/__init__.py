"""Models a case where Dagster is used purely for orchestration and not data transformation.

In this scenario, both the structure of the asset graph and the compute logic for assets are
defined externally to Dagster. The asset graph is specified in a schema, and an external system
knows how to compute each asset listed in this schema.

We integrate the system with Dagster by using an asset factory to construct Dagster
`AssetsDefinition` objects for each node in the asset graph. Dagster forwards materialization
requests to the external system. We pass an asset specification together with provenance information
for the last materialization of the asset on record. The external system is responsible for
correctly processing this information-- if the provenance of the last materialization is stale
(different from the current state of the asset), then it should recompute the asset and overwrite
the existing value. Otherwise, it should simply use the existing stored value of the asset.

The materialization endpoint of the external system returns a data version string and a flag
indicating whether a memoized value was used. This information is passed to the Dagster framework by
returning a `Nothing` `Output`.
"""

import warnings
from typing import Sequence, cast

from dagster import (
    AssetKey,
    AssetsDefinition,
    AssetSelection,
    DataProvenance,
    DataVersion,
    Definitions,
    ExperimentalWarning,
    In,
    Nothing,
    OpDefinition,
    OpExecutionContext,
    Out,
    Output,
    SourceAsset,
    define_asset_job,
)
from typing_extensions import TypedDict

from dagster_test.toys.user_computed_data_versions.external_system import (
    AssetInfo,
    ExternalSystem,
    ProvenanceSpec,
    SourceAssetInfo,
)

warnings.filterwarnings("ignore", category=ExperimentalWarning)


def external_asset(asset_spec: AssetInfo):
    """Factory to build an `AssetsDefinition` object to represent an asset externally defined by an
    `AssetInfo`.

    The op attached to the `AssetsDefinition` forwards materialization requests to the external
    system, sending an asset key and provenance info for the last recorded materialization of the
    asset. The external system responds with a data version and a flag indicating whether a memoized
    value was used for the materialization (i.e. whether recomputation occurred). This is passed to
    the dagster framework by packaging it on a returned `Output` object. The `Output` returns
    `Nothing` because Dagster is not handling passing data in between ops in this scenario.

    Args:
        asset_spec (AssetInfo):
            A dictionary containing the metadata that defines the asset.

    Returns (AssetsDefinition):
        An `AssetsDefinition` instance representing the asset in the external system.
    """
    key = AssetKey([asset_spec["key"]])
    code_version = asset_spec["code_version"]
    dependencies = {AssetKey([dep]) for dep in asset_spec["dependencies"]}

    def fn(context: OpExecutionContext, *args):
        external_system = ExternalSystem(context.instance.storage_directory())

        provenance = context.get_asset_provenance(key)
        provenance_spec = provenance_to_dict(provenance) if provenance else None
        result = external_system.materialize(
            asset_spec,
            provenance_spec,
        )
        if result["is_memoized"]:
            context.log.info(f"Used memoized value for {key.to_user_string()}")
        yield Output(
            None,
            data_version=DataVersion(result["data_version"]),
            metadata={"is_memoized": result["is_memoized"]},
        )

    keys_by_input_name = {k.path[-1]: k for k in dependencies}
    keys_by_output_name = {"result": key}
    op_def = OpDefinition(
        name=key.path[-1],
        ins={k.to_user_string(): In(cast(type, Nothing)) for k in dependencies},
        outs={"result": Out(Nothing)},
        code_version=code_version,
        compute_fn=fn,
    )
    return AssetsDefinition(
        keys_by_input_name=keys_by_input_name,
        keys_by_output_name=keys_by_output_name,
        node_def=op_def,
    )


def external_source_asset(source_asset_spec: SourceAssetInfo) -> SourceAsset:
    """Factory to build a `SourceAsset` object to represent a source asset externally defined by a `SourceAssetInfo`.

    The op attached to the `SourceAsset` forwards observation requests to the external system. The
    external system responds with the current data version of the asset.

    Args:
        source_asset_spec (SourceAssetInfo):
            A dictionary containing the metadata that defines the source asset.

    Returns (SourceAsset):
        A `SourceAsset` instance representing the source asset in the external system.
    """
    key = AssetKey([source_asset_spec["key"]])

    def fn(context) -> DataVersion:
        external_system = ExternalSystem(context.instance.storage_directory())
        result = external_system.observe(source_asset_spec)
        return DataVersion(result["data_version"])

    return SourceAsset(key, observe_fn=fn)


def provenance_to_dict(provenance: DataProvenance) -> ProvenanceSpec:
    return {
        "code_version": provenance.code_version,
        "input_data_versions": {
            key.to_user_string(): version.value
            for key, version in provenance.input_data_versions.items()
        },
    }


# ########################
# ##### DEFINITIONS
# ########################


class Schema(TypedDict):
    assets: Sequence[AssetInfo]
    source_assets: Sequence[SourceAssetInfo]


SCHEMA: Schema = {
    "assets": [
        {"key": "alpha", "code_version": "lib/v1", "dependencies": set()},
        {"key": "beta", "code_version": "lib/v1", "dependencies": {"alpha"}},
        {"key": "epsilon", "code_version": "lib/v1", "dependencies": {"delta"}},
    ],
    "source_assets": [
        {"key": "delta"},
    ],
}

assets = [external_asset(asset_spec) for asset_spec in SCHEMA["assets"]]
source_assets = [
    external_source_asset(source_asset_spec) for source_asset_spec in SCHEMA["source_assets"]
]


defs = Definitions(
    assets=[*assets, *source_assets],
    jobs=[define_asset_job("external_system_job", AssetSelection.assets("alpha", "beta"))],
)
