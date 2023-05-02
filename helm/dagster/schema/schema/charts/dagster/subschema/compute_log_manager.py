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
    storageAccount: StringSource
    container: StringSource
    secretKey: Optional[StringSource]
    defaultAzureCredential: Optional[dict]
    localDir: Optional[StringSource]
    prefix: Optional[StringSource]
    uploadInterval: Optional[int]


class GCSComputeLogManager(BaseModel):
    bucket: StringSource
    localDir: Optional[StringSource]
    prefix: Optional[StringSource]
    jsonCredentialsEnvvar: Optional[StringSource]
    uploadInterval: Optional[int]


class S3ComputeLogManager(BaseModel):
    bucket: StringSource
    localDir: Optional[StringSource]
    prefix: Optional[StringSource]
    useSsl: Optional[bool]
    verify: Optional[bool]
    verifyCertPath: Optional[StringSource]
    endpointUrl: Optional[StringSource]
    skipEmptyFiles: Optional[bool]
    uploadInterval: Optional[int]
    uploadExtraArgs: Optional[dict]
    showUrlOnly: Optional[bool]
    region: Optional[StringSource]


class ComputeLogManagerConfig(BaseModel):
    azureBlobComputeLogManager: Optional[AzureBlobComputeLogManager]
    gcsComputeLogManager: Optional[GCSComputeLogManager]
    s3ComputeLogManager: Optional[S3ComputeLogManager]
    customComputeLogManager: Optional[ConfigurableClass]

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
