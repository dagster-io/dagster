from enum import Enum
from typing import Any, Mapping, Sequence, Union, cast

from dagster import (
    AssetCheckSpec,
    AssetSpec,
    _check as check,
)
from dagster._record import record
from dagster._serdes.serdes import whitelist_for_serdes
from dagster._utils.names import clean_asset_name


@whitelist_for_serdes
@record
class DbtCloudProjectEnvironmentData:
    project_id: int
    environment_id: int
    # The dbt cloud job id that we'll use to kick off executions launched from a client.
    job_id: int
    models_by_unique_id: Mapping[str, "DbtCloudContentData"]
    sources_by_unique_id: Mapping[str, "DbtCloudContentData"]
    tests_by_unique_id: Mapping[str, "DbtCloudContentData"]


@whitelist_for_serdes
class DbtCloudContentType(Enum):
    MODEL = "MODEL"
    SOURCE = "SOURCE"
    TEST = "TEST"


@whitelist_for_serdes
@record
class DbtCloudContentData:
    content_type: DbtCloudContentType
    properties: Mapping[str, Any]

    def from_raw_gql(self, raw_data: Mapping[str, Any]) -> "DbtCloudContentData":
        content_type = DbtCloudContentType(raw_data["resourceType"].upper())
        return DbtCloudContentData(content_type=content_type, properties=raw_data["properties"])


class DagsterDbtCloudTranslator:
    """Translator class which converts raw response data from the dbt Cloud API into AssetSpecs.
    Subclass this class to implement custom logic for each type of dbt Cloud content.
    """

    def __init__(self, context: DbtCloudProjectEnvironmentData):
        self._context = context

    @property
    def environment_data(self) -> DbtCloudProjectEnvironmentData:
        return self._context

    def get_model_spec(self, data: DbtCloudContentData) -> AssetSpec:
        # This is obviously a placeholder implementation
        return AssetSpec(key=clean_asset_name(data.properties["uniqueId"]))

    def get_source_spec(self, data: DbtCloudContentData) -> AssetSpec:
        # This is obviously a placeholder implementation
        return AssetSpec(key=clean_asset_name(data.properties["uniqueId"]))

    def get_test_spec(self, data: DbtCloudContentData) -> AssetCheckSpec:
        associated_data_per_parent = []
        for parent in data.properties["parents"]:
            if parent["resourceType"] == "model":
                associated_data_per_parent.append(
                    self.environment_data.models_by_unique_id[parent["uniqueId"]]
                )
            elif parent["resourceType"] == "source":
                associated_data_per_parent.append(
                    self.environment_data.sources_by_unique_id[parent["uniqueId"]]
                )
            else:
                # Macros, etc. which we don't create assets for.
                continue
        # Haven't actually figured out if it's possible for there to be more than one "asset-creatable" entity per test
        parent_specs = cast(
            Sequence[AssetSpec], [self.get_spec(data) for data in associated_data_per_parent]
        )
        check.invariant(len(parent_specs) > 0, "Must have at least one parent asset for a check.")
        return AssetCheckSpec(
            name=clean_asset_name(data.properties["uniqueId"]),
            asset=parent_specs[0].key,
            additional_deps=[parent_spec.key for parent_spec in parent_specs[1:]],
        )

    def get_spec(self, data: DbtCloudContentData) -> Union[AssetSpec, AssetCheckSpec]:
        if data.content_type == DbtCloudContentType.MODEL:
            return self.get_model_spec(data)
        elif data.content_type == DbtCloudContentType.SOURCE:
            return self.get_source_spec(data)
        elif data.content_type == DbtCloudContentType.TEST:
            return self.get_test_spec(data)
        else:
            raise Exception(f"Unrecognized content type: {data.content_type}")
