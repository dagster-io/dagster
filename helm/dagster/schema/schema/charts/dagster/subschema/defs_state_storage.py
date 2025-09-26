from enum import Enum
from typing import Optional

from pydantic import ConfigDict, Field

from schema.charts.dagster.subschema.config import StringSource
from schema.charts.utils.utils import BaseModel, create_json_schema_conditionals


class DefsStateStorageType(str, Enum):
    BLOB_STORAGE = "BlobStorageStateStorage"
    CUSTOM = "CustomDefsStateStorage"


class BlobStorageStateStorage(BaseModel):
    basePath: StringSource
    storageOptions: Optional[dict] = None


class CustomDefsStateStorage(BaseModel):
    module: StringSource
    class_: StringSource = Field(alias="class")
    config: Optional[dict] = None


class DefsStateStorageConfig(BaseModel):
    blobStorageStateStorage: Optional[BlobStorageStateStorage] = None
    customDefsStateStorage: Optional[CustomDefsStateStorage] = None


class DefsStateStorage(BaseModel):
    type: DefsStateStorageType
    config: Optional[DefsStateStorageConfig] = None

    model_config = ConfigDict(
        json_schema_extra=create_json_schema_conditionals(
            {
                DefsStateStorageType.BLOB_STORAGE: "blobStorageStateStorage",
                DefsStateStorageType.CUSTOM: "customDefsStateStorage",
            }
        )
    )
