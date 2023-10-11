fn main() {
    let mut pipes = open_dagster_pipes();
    let null_count = check_large_dataframe_for_nulls(pipes.partition_key);
    let passed = null_count == 0;
    let metadata = json!({"null_count": {"raw_value": null_count, "type": "int"}});

    report_asset_check(
        pipes,
        "telem_post_processing_check",
        passed,
        "telem_post_processing",
        metadata,
    );
}