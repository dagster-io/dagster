# Stubs have been sourced from
#
#    https://youtype.github.io/boto3_stubs_docs/mypy_boto3_s3/type_defs/#objecttypedef
#
# as to not require any additional dependencies

from datetime import datetime
from typing import Literal, TypedDict

ChecksumAlgorithmType = Literal[
    "CRC32",
    "CRC32C",
    "SHA1",
    "SHA256",
]

ObjectStorageClassType = Literal[
    "DEEP_ARCHIVE",
    "EXPRESS_ONEZONE",
    "GLACIER",
    "GLACIER_IR",
    "INTELLIGENT_TIERING",
    "ONEZONE_IA",
    "OUTPOSTS",
    "REDUCED_REDUNDANCY",
    "SNOW",
    "STANDARD",
    "STANDARD_IA",
]


class OwnerTypeDef(TypedDict):
    DisplayName: str | None
    ID: str | None


class RestoreStatusTypeDef(TypedDict):
    IsRestoreInProgress: bool | None
    RestoreExpiryDate: datetime | None


class ObjectTypeDef(TypedDict):
    Key: str
    LastModified: datetime
    ETag: str | None
    ChecksumAlgorithm: list[ChecksumAlgorithmType] | None
    Size: int | None
    StorageClass: ObjectStorageClassType | None
    Owner: OwnerTypeDef | None
    RestoreStatus: RestoreStatusTypeDef | None
