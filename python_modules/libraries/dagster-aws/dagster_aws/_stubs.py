# Stubs have been sourced from
#
#    https://youtype.github.io/boto3_stubs_docs/mypy_boto3_s3/type_defs/#objecttypedef
#
# as to not require any additional dependencies

from datetime import datetime
from typing import Literal, Optional, TypedDict

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
    DisplayName: Optional[str]
    ID: Optional[str]


class RestoreStatusTypeDef(TypedDict):
    IsRestoreInProgress: Optional[bool]
    RestoreExpiryDate: Optional[datetime]


class ObjectTypeDef(TypedDict):
    Key: str
    LastModified: datetime
    ETag: Optional[str]
    ChecksumAlgorithm: Optional[list[ChecksumAlgorithmType]]
    Size: Optional[int]
    StorageClass: Optional[ObjectStorageClassType]
    Owner: Optional[OwnerTypeDef]
    RestoreStatus: Optional[RestoreStatusTypeDef]
