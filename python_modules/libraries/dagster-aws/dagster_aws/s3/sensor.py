from typing import Optional

import boto3
import dagster._check as check


class ClientException(Exception):
    pass


def get_s3_keys(
    bucket: str,
    prefix: str = "",
    since_key: Optional[str] = None,
    s3_session: Optional[boto3.Session] = None,
):
    check.str_param(bucket, "bucket")
    check.str_param(prefix, "prefix")
    check.opt_str_param(since_key, "since_key")

    if not s3_session:
        s3_session = boto3.client("s3", use_ssl=True, verify=True)

    if not s3_session:
        raise ClientException("Failed to initialize s3 client")

    paginator = s3_session.get_paginator("list_objects_v2")  # type: ignore
    page_iterator = paginator.paginate(Bucket=bucket, Prefix=prefix)

    contents = []
    for page in page_iterator:
        contents.extend(page.get("Contents", []))

    sorted_keys = [obj["Key"] for obj in sorted(contents, key=lambda x: x["LastModified"])]

    if not since_key or since_key not in sorted_keys:
        return sorted_keys

    for idx, key in enumerate(sorted_keys):
        if key == since_key:
            return sorted_keys[idx + 1 :]

    return []
