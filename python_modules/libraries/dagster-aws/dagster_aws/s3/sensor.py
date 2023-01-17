import boto3
import dagster._check as check

MAX_KEYS = 1000


def get_s3_keys(bucket, prefix="", since_key=None, s3_session=None):
    check.str_param(bucket, "bucket")
    check.str_param(prefix, "prefix")
    check.opt_str_param(since_key, "since_key")

    if not s3_session:
        s3_session = boto3.resource("s3", use_ssl=True, verify=True).meta.client

    cursor = ""
    contents = []

    while True:
        response = s3_session.list_objects_v2(
            Bucket=bucket,
            Delimiter="",
            MaxKeys=MAX_KEYS,
            Prefix=prefix,
            StartAfter=cursor,
        )
        contents.extend(response.get("Contents", []))
        if response["KeyCount"] < MAX_KEYS:
            break

        cursor = response["Contents"][-1]["Key"]

    sorted_keys = [obj["Key"] for obj in sorted(contents, key=lambda x: x["LastModified"])]

    if not since_key or since_key not in sorted_keys:
        return sorted_keys

    for idx, key in enumerate(sorted_keys):
        if key == since_key:
            return sorted_keys[idx + 1 :]

    return []
