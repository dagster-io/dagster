# ruff: isort: skip_file
from docs_snippets.concepts.assets.non_argument_deps import (
    shopping_list,
    sugary_cereals,
)


# start_marker
from dagster import Definitions, define_asset_job


all_assets_job = define_asset_job(name="all_assets_job")
sugary_cereals_job = define_asset_job(
    name="sugary_cereals_job", selection="sugary_cereals"
)

defs = Definitions(
    assets=[sugary_cereals, shopping_list],
    jobs=[all_assets_job, sugary_cereals_job],
)

# end_marker
