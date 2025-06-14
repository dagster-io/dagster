from my_project.defs.assets import loaded_file

import dagster as dg


# highlight-start
def test_loaded_file() -> None:
    context = dg.build_asset_context(partition_key="2024-08-16")
    assert loaded_file(context) == "Contents for August 16th, 2024"
    # highlight-end
