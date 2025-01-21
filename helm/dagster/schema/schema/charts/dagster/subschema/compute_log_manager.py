from enum import Enum
from typing import Any, Optional

from pydantic import ConfigDict

from schema.charts.dagster.subschema.config import StringSource
from schema.charts.utils.utils import BaseModel, ConfigurableClass, create_json_schema_conditionals


class ComputeLogManagerType(str, Enum):
    NOOP = "NoOpComputeLogManager"
    AZURE = "AzureBlobComputeLogManager"
    GCS = "GCSComputeLogManager"
    S3 = "S3ComputeLogManager"
    LOCAL = "LocalComputeLogManager"
    CUSTOM = "CustomComputeLogManager"


class AzureBlobComputeLogManager(BaseModel):
    storageAccount: StringSource
    container: StringSource
    secretCredential: Optional[dict] = None
    defaultAzureCredential: Optional[dict] = None
    accessKeyOrSasToken: Optional[StringSource] = None
    localDir: Optional[StringSource] = None
    prefix: Optional[StringSource] = None
    uploadInterval: Optional[int] = None
    showUrlOnly: Optional[bool] = None


class GCSComputeLogManager(BaseModel):
    bucket: StringSource
    localDir: Optional[StringSource] = None
    prefix: Optional[StringSource] = None
    jsonCredentialsEnvvar: Optional[StringSource] = None
    uploadInterval: Optional[int] = None
    showUrlOnly: Optional[bool] = None


class S3ComputeLogManager(BaseModel):
    bucket: StringSource
    localDir: Optional[StringSource] = None
    prefix: Optional[StringSource] = None
    useSsl: Optional[bool] = None
    verify: Optional[bool] = None
    verifyCertPath: Optional[StringSource] = None
    endpointUrl: Optional[StringSource] = None
    skipEmptyFiles: Optional[bool] = None
    uploadInterval: Optional[int] = None
    uploadExtraArgs: Optional[dict] = None
    showUrlOnly: Optional[bool] = None
    region: Optional[StringSource] = None


class LocalComputeLogManager(BaseModel):
    baseDir: StringSource
    pollingTimeout: Optional[int] = None


class ComputeLogManagerConfig(BaseModel, extra="forbid"):
    azureBlobComputeLogManager: Optional[AzureBlobComputeLogManager] = None
    gcsComputeLogManager: Optional[GCSComputeLogManager] = None
    s3ComputeLogManager: Optional[S3ComputeLogManager] = None
    localComputeLogManager: Optional[LocalComputeLogManager] = None
    customComputeLogManager: Optional[ConfigurableClass] = None


class ComputeLogManager(BaseModel):
    type: ComputeLogManagerType
    config: ComputeLogManagerConfig

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra=lambda schema, model: ComputeLogManager.json_schema_extra(schema, model),
    )

    @staticmethod
    def json_schema_extra(schema: dict[str, Any], model: type["ComputeLogManager"]):
        schema["allOf"] = create_json_schema_conditionals(
            {
                ComputeLogManagerType.AZURE: "azureBlobComputeLogManager",
                ComputeLogManagerType.GCS: "gcsComputeLogManager",
                ComputeLogManagerType.S3: "s3ComputeLogManager",
                ComputeLogManagerType.LOCAL: "localComputeLogManager",
                ComputeLogManagerType.CUSTOM: "customComputeLogManager",
            }
        )
