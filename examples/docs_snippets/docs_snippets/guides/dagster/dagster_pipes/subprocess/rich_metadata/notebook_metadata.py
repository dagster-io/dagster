def get_notebook_path(args): ...


context = ...

# start_notebook
# Within the Dagster pipes subprocess:
notebook_path = "/path/to/notebook.ipynb"
# Then, when reporting the asset materialization:
context.report_asset_materialization(
    asset_key="foo",
    metadata={"notebook_meta": {"type": "notebook", "raw_value": notebook_path}},
)
# end_notebook
