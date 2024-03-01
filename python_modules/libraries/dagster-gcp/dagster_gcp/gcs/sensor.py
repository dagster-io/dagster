import dagster._check as check
from google.cloud import storage

MAX_KEYS = 1000


def get_gcs_keys(bucket, prefix="", since_key=None, gcs_session=None):
    check.str_param(bucket, "bucket")
    check.str_param(prefix, "prefix")
    check.opt_str_param(since_key, "since_key")

    if not gcs_session:
        gcs_session = storage.Client()

    contents = list(
        gcs_session.list_blobs(
            bucket_or_name=bucket,
            delimiter="",
            page_size=MAX_KEYS,
            prefix=prefix,
        )
    )

    sorted_keys = [obj.name for obj in sorted(contents, key=lambda x: x.updated)]

    if not since_key or since_key not in sorted_keys:
        return sorted_keys

    for idx, key in enumerate(sorted_keys):
        if key == since_key:
            return sorted_keys[idx + 1:]

    return []
