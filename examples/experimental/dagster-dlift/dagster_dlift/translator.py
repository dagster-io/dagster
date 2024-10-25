from enum import Enum
from typing import Any, Mapping, NamedTuple, Union

from dagster import AssetCheckSpec, AssetSpec


class DbtCloudProjectEnvironmentData(NamedTuple):
    project_id: int
    environment_id: int
    models_by_unique_id: Mapping[str, "DbtCloudContentData"]
    sources_by_unique_id: Mapping[str, "DbtCloudContentData"]
    tests_by_unique_id: Mapping[str, "DbtCloudContentData"]


class DbtCloudContentType(Enum):
    MODEL = "MODEL"
    SOURCE = "SOURCE"
    TEST = "TEST"


class DbtCloudContentData(NamedTuple):
    content_type: DbtCloudContentType
    properties: Mapping[str, Any]


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
        return AssetSpec(key=data.properties["uniqueId"])

    def get_source_spec(self, data: DbtCloudContentData) -> AssetSpec:
        # This is obviously a placeholder implementation
        return AssetSpec(key=data.properties["uniqueId"])

    def get_test_spec(self, data: DbtCloudContentData) -> AssetCheckSpec:
        # This is obviously a placeholder implementation
        return AssetCheckSpec(name=data.properties["uniqueId"], asset=data.properties["uniqueId"])

    def get_spec(self, data: DbtCloudContentData) -> Union[AssetSpec, AssetCheckSpec]:
        if data.content_type == DbtCloudContentType.MODEL:
            return self.get_model_spec(data)
        elif data.content_type == DbtCloudContentType.SOURCE:
            return self.get_source_spec(data)
        elif data.content_type == DbtCloudContentType.TEST:
            return self.get_test_spec(data)
        else:
            raise Exception(f"Unrecognized content type: {data.content_type}")
