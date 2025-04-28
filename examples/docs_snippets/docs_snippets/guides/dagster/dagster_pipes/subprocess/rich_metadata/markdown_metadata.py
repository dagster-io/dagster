def get_markdown_content(args): ...


context = ...

# start_markdown
# Within the Dagster pipes subprocess:
markdown_content = "# Header\nSome **bold** text"
# Then, when reporting the asset materialization:
context.report_asset_materialization(
    asset_key="foo",
    metadata={"md_meta": {"type": "md", "raw_value": markdown_content}},
)
# end_markdown
