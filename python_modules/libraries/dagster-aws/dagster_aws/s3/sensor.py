from datetime import datetime
from typing import Any, Optional, cast

import boto3
import dagster._check as check
from dagster._annotations import deprecated

from dagster_aws._stubs import ObjectTypeDef


class ClientException(Exception):
    pass


def get_objects(
    bucket: str,
    prefix: str = "",
    since_key: Optional[str] = None,
    since_last_modified: Optional[datetime] = None,
    client=None,
) -> list[ObjectTypeDef]:
    """Retrieves a list of object keys in S3 for a given `bucket`, `prefix`, and filter option.

    Args:
        bucket (str): s3 bucket
        prefix (str): s3 object prefix
        since_key (Optional[str]): retrieve objects modified after the last modified timestamp of this key
        since_last_modified (Optional[datetime]): retrieve objects after this timestamp (non-inclusive)
        client (Optional[boto3.Client]): s3 client

    Returns:
        List of object keys in S3.

    """
    check.str_param(bucket, "bucket")
    check.str_param(prefix, "prefix")
    check.opt_str_param(since_key, "since_key")
    check.opt_inst_param(since_last_modified, "since_last_modified", datetime)

    if not client:
        client = boto3.client("s3")

    if not client:
        raise ClientException("Failed to initialize s3 client")

    paginator = client.get_paginator("list_objects_v2")
    page_iterator = paginator.paginate(Bucket=bucket, Prefix=prefix, Delimiter="")

    objects: list[ObjectTypeDef] = []
    for page in page_iterator:
        contents = page.get("Contents", [])
        objects.extend([cast(ObjectTypeDef, obj) for obj in contents])

    if since_key and not any(obj.get("Key") == since_key for obj in objects):
        raise Exception("Provided `since_key` is not present in list of objects")

    sorted_objects = [obj for obj in sorted(objects, key=lambda x: x.get("LastModified"))]

    if since_key:
        for idx, obj in enumerate(sorted_objects):
            if obj.get("Key") == since_key:
                return sorted_objects[idx + 1 :]

    if since_last_modified:
        for idx, obj in enumerate(sorted_objects):
            if obj.get("LastModified") > since_last_modified:
                return sorted_objects[idx:]

    return sorted_objects


@deprecated(breaking_version="2.0", additional_warn_text="Use get_objects instead.")
def get_s3_keys(
    bucket: str,
    prefix: str = "",
    since_key: Optional[str] = None,
    s3_session: Optional[Any] = None,
) -> list[str]:
    """Retrieves a list of object keys in S3 for a given `bucket`, `prefix`, and filter option.

    Note: when using the `since_key` it is possible to miss records if that key has been modified,
    as sorting is done by the `LastModified` property of the S3 object. For more information, see
    the following GitHub issue:

        https://github.com/dagster-io/dagster/issues/22892

    Args:
        bucket (str): s3 bucket
        prefix (str): s3 object prefix
        since_key (Optional[str]): retrieve objects after the modified date of this key
        since_last_modified (Optional[str]): retrieve objects after this timestamp
        s3_session (Optional[boto3.Client]): s3 client

    Returns:
        List of object keys in S3.

    """
    objects = get_objects(bucket=bucket, prefix=prefix, since_key=since_key, client=s3_session)
    return [obj.get("Key") for obj in objects]
