from enum import Enum
from typing import Any, Dict, Optional, Type

from pydantic import Extra

from ...utils.utils import BaseModel, ConfigurableClass, create_json_schema_conditionals
from .config import StringSource


class ComputeLogManagerType(str, Enum):
    NOOP = "NoOpComputeLogManager"
    AZURE = "AzureBlobComputeLogManager"
    GCS = "GCSComputeLogManager"
    S3 = "S3ComputeLogManager"
    CUSTOM = "CustomComputeLogManager"


class AzureBlobComputeLogManager(BaseModel):
    secretKey: Optional[StringSource] = None
    defaultAzureCredential: Optional[dict] = None
    localDir: Optional[StringSource] = None
    prefix: Optional[StringSource] = None
    uploadInterval: Optional[int] = None

    storageAccount: StringSource
    container: StringSource


class GCSComputeLogManager(BaseModel):
    localDir: Optional[StringSource] = None
    prefix: Optional[StringSource] = None
    jsonCredentialsEnvvar: Optional[StringSource] = None
    uploadInterval: Optional[int] = None
    bucket: StringSource


class S3ComputeLogManager(BaseModel):
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
    bucket: StringSource


class ComputeLogManagerConfig(BaseModel):
    azureBlobComputeLogManager: Optional[AzureBlobComputeLogManager] = None
    gcsComputeLogManager: Optional[GCSComputeLogManager] = None
    s3ComputeLogManager: Optional[S3ComputeLogManager] = None
    customComputeLogManager: Optional[ConfigurableClass] = None

    class Config:
        extra = Extra.forbid


class ComputeLogManager(BaseModel):
    type: ComputeLogManagerType
    config: ComputeLogManagerConfig

    class Config:
        extra = Extra.forbid

        @staticmethod
        def schema_extra(schema: Dict[str, Any], model: Type["ComputeLogManager"]):
            BaseModel.Config.schema_extra(schema, model)
            schema["allOf"] = create_json_schema_conditionals(
                {
                    ComputeLogManagerType.AZURE: "azureBlobComputeLogManager",
                    ComputeLogManagerType.GCS: "gcsComputeLogManager",
                    ComputeLogManagerType.S3: "s3ComputeLogManager",
                    ComputeLogManagerType.CUSTOM: "customComputeLogManager",
                }
            )
