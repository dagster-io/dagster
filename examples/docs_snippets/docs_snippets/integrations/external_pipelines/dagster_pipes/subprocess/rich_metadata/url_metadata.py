def get_url(args): ...


context = ...

# start_url
# Within the Dagster pipes subprocess:
url = "http://example.com"
# Then, when reporting the asset materialization:
context.report_asset_materialization(
    asset_key="foo",
    metadata={"url_meta": {"type": "url", "raw_value": url}},
)
# end_url
