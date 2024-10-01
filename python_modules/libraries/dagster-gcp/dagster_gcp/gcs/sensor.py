import dagster._check as check
from google.cloud import storage

MAX_KEYS = 1000


def get_gcs_keys(bucket, prefix=None, since_key=None, gcs_session=None):
    """Return a list of updated keys in a GCS bucket.

    Args:
        bucket (str): The name of the GCS bucket.
        prefix (Optional[str]): The prefix to filter the keys by.
        since_key (Optional[str]): The key to start from. If provided, only keys updated after this key will be returned.
        gcs_session (Optional[google.cloud.storage.client.Client]): A GCS client session. If not provided, a new session will be created.

    Returns:
        List[str]: A list of keys in the bucket, sorted by update time, that are newer than the `since_key`.

    Example:
        .. code-block:: python

            @resource
            def google_cloud_storage_client(context):
                return storage.Client().from_service_account_json("my-service-account.json")

            @sensor(job=my_job, required_resource_keys={"google_cloud_storage_client"})
            def my_gcs_sensor(context):
                since_key = context.cursor or None
                new_gcs_keys = get_gcs_keys(
                    "my-bucket",
                    prefix="data",
                    since_key=since_key,
                    gcs_session=context.resources.google_cloud_storage_client
                )

                if not new_gcs_keys:
                    return SkipReason("No new gcs files found for bucket 'my-bucket'.")

                for gcs_key in new_gcs_keys:
                    yield RunRequest(run_key=gcs_key, run_config={
                        "ops": {
                            "gcs_files": {
                                "config": {
                                    "gcs_key": gcs_key
                                }
                            }
                        }
                    })

                last_key = new_gcs_keys[-1]
                context.update_cursor(last_key)
    """
    check.str_param(bucket, "bucket")
    check.opt_str_param(prefix, "prefix")
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
            return sorted_keys[idx + 1 :]

    return []
