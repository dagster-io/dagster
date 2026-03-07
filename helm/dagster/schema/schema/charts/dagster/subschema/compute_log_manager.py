from enum import Enum
from typing import Any

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
    secretCredential: dict | None = None
    defaultAzureCredential: dict | None = None
    accessKeyOrSasToken: StringSource | None = None
    localDir: StringSource | None = None
    prefix: StringSource | None = None
    uploadInterval: int | None = None
    showUrlOnly: bool | None = None


class GCSComputeLogManager(BaseModel):
    bucket: StringSource
    localDir: StringSource | None = None
    prefix: StringSource | None = None
    jsonCredentialsEnvvar: StringSource | None = None
    uploadInterval: int | None = None
    showUrlOnly: bool | None = None


class S3ComputeLogManager(BaseModel):
    bucket: StringSource
    localDir: StringSource | None = None
    prefix: StringSource | None = None
    useSsl: bool | None = None
    verify: bool | None = None
    verifyCertPath: StringSource | None = None
    endpointUrl: StringSource | None = None
    skipEmptyFiles: bool | None = None
    uploadInterval: int | None = None
    uploadExtraArgs: dict | None = None
    showUrlOnly: bool | None = None
    region: StringSource | None = None


class LocalComputeLogManager(BaseModel):
    baseDir: StringSource
    pollingTimeout: int | None = None


class ComputeLogManagerConfig(BaseModel, extra="forbid"):
    azureBlobComputeLogManager: AzureBlobComputeLogManager | None = None
    gcsComputeLogManager: GCSComputeLogManager | None = None
    s3ComputeLogManager: S3ComputeLogManager | None = None
    localComputeLogManager: LocalComputeLogManager | None = None
    customComputeLogManager: ConfigurableClass | None = None


class ComputeLogManager(BaseModel):
    type: ComputeLogManagerType
    config: ComputeLogManagerConfig

    model_config = ConfigDict(
        extra="forbid",
        # Lambda required: defers evaluation until class is fully defined
        json_schema_extra=lambda schema, model: ComputeLogManager.json_schema_extra(schema, model),  # noqa: PLW0108
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
