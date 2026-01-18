def get_timestamp_data(args): ...


context = ...

# start_timestamp
# Within the Dagster pipes subprocess:
timestamp = 1234567890
# Then, when reporting the asset materialization:
context.report_asset_materialization(
    asset_key="foo",
    metadata={"timestamp_meta": {"type": "timestamp", "raw_value": timestamp}},
)
# end_timestamp
