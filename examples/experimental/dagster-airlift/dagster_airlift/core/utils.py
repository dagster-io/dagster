from typing import List, Optional, Sequence, Union, cast

from dagster import (
    AssetsDefinition,
    AssetSpec,
    JsonMetadataValue,
    _check as check,
)
from dagster._core.definitions.utils import VALID_NAME_REGEX
from dagster._core.storage.tags import KIND_PREFIX

from dagster_airlift.constants import AIRFLOW_COUPLING_METADATA_KEY, AirflowCoupling


def convert_to_valid_dagster_name(name: str) -> str:
    """Converts a name to a valid dagster name by replacing invalid characters with underscores. / is converted to a double underscore."""
    return "".join(c if VALID_NAME_REGEX.match(c) else "__" if c == "/" else "_" for c in name)


def get_couplings_from_asset(
    asset: Union[AssetsDefinition, AssetSpec],
) -> Optional[Sequence[AirflowCoupling]]:
    specs = asset.specs if isinstance(asset, AssetsDefinition) else [asset]
    asset_name = (
        asset.node_def.name
        if isinstance(asset, AssetsDefinition) and asset.is_executable
        else asset.key.to_user_string()
    )
    if any(AIRFLOW_COUPLING_METADATA_KEY in spec.metadata for spec in specs):
        prop: Optional[JsonMetadataValue] = None
        for spec in specs:
            if prop is None:
                prop = spec.metadata[AIRFLOW_COUPLING_METADATA_KEY]
            else:
                if spec.metadata.get(AIRFLOW_COUPLING_METADATA_KEY) is None:
                    check.failed(
                        f"Missing {AIRFLOW_COUPLING_METADATA_KEY} tag in spec {spec.key} for {asset_name}"
                    )
                check.invariant(
                    prop == spec.metadata[AIRFLOW_COUPLING_METADATA_KEY],
                    f"Task ID mismatch within same AssetsDefinition: {prop} != {spec.metadata[AIRFLOW_COUPLING_METADATA_KEY]}",
                )
        return cast(List[AirflowCoupling], cast(JsonMetadataValue, prop).value)
    return None


def airflow_kind_dict() -> dict:
    return {f"{KIND_PREFIX}airflow": ""}
