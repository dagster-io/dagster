from collections.abc import Mapping, Sequence
from enum import Enum
from typing import Any, Union, cast

from dagster import (
    AssetCheckResult,
    AssetCheckSpec,
    AssetMaterialization,
    AssetSpec,
    _check as check,
)
from dagster._core.storage.tags import KIND_PREFIX
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

    def get_from_unique_id(self, unique_id: str) -> "DbtCloudContentData":
        if unique_id in self.models_by_unique_id:
            return self.models_by_unique_id[unique_id]
        if unique_id in self.sources_by_unique_id:
            return self.sources_by_unique_id[unique_id]
        if unique_id in self.tests_by_unique_id:
            return self.tests_by_unique_id[unique_id]
        raise Exception(f"Unique id {unique_id} not found in environment data.")


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
        return AssetSpec(
            key=clean_asset_name(data.properties["uniqueId"]),
            metadata={"raw_data": data.properties},
            tags={f"{KIND_PREFIX}dbt": ""},
        )

    def get_source_spec(self, data: DbtCloudContentData) -> AssetSpec:
        # This is obviously a placeholder implementation
        return AssetSpec(
            key=clean_asset_name(data.properties["uniqueId"]),
            metadata={"raw_data": data.properties},
            tags={f"{KIND_PREFIX}dbt": ""},
        )

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
            metadata={"raw_data": data.properties},
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

    def get_asset_event(
        self, spec: Union[AssetSpec, AssetCheckSpec], result: Mapping[str, Any]
    ) -> Union[AssetMaterialization, AssetCheckResult]:
        if isinstance(spec, AssetSpec):
            return self.get_materialization(spec, result)
        else:
            return self.get_check_result(spec, result)

    def get_materialization(
        self, spec: AssetSpec, result: Mapping[str, Any]
    ) -> AssetMaterialization:
        return AssetMaterialization(spec.key)

    def get_check_result(self, spec: AssetCheckSpec, result: Mapping[str, Any]) -> AssetCheckResult:
        return AssetCheckResult(
            passed=True if result["status"] == "pass" else False,
            check_name=spec.name,
            asset_key=spec.key.asset_key,
        )
