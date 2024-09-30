from typing import Optional
import boto3
import dagster._check as check


def get_s3_keys(bucket: str, prefix: str = "", since_key: Optional[str] = None, s3_session: boto3.Session = None):
    check.str_param(bucket, "bucket")
    check.str_param(prefix, "prefix")
    check.opt_str_param(since_key, "since_key")

    if not s3_session:
        s3_session = boto3.resource("s3", use_ssl=True, verify=True).meta.client

    contents = []
    continuation_token = None

    while True:
        params = {
            "Bucket": bucket,
            "Prefix": prefix,
        }
        if continuation_token:
            params["ContinuationToken"] = continuation_token

        response = s3_session.list_objects_v2(**params)
        contents.extend(response.get("Contents", []))

        if not response.get("IsTruncated"):
            break

        continuation_token = response.get("NextContinuationToken")

    sorted_keys = [obj["Key"] for obj in sorted(contents, key=lambda x: x["LastModified"])]

    if not since_key or since_key not in sorted_keys:
        return sorted_keys

    for idx, key in enumerate(sorted_keys):
        if key == since_key:
            return sorted_keys[idx + 1 :]

    return []
