def on_s3_file_uploaded(s3_path):
    requests.post(
        url=f"{DAGSTER_URL}/report_asset_materialization/",
        json={"asset_key": key_from_path(s3_path)},
    ).raise_for_status()
