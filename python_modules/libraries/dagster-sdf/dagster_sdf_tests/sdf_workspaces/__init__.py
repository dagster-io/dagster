from pathlib import Path

projects_path = Path(__file__).joinpath("..").resolve()

lineage_path = projects_path.joinpath("lineage")
lineage_upstream_path = projects_path.joinpath("lineage_upstream")
lineage_asset_checks_path = projects_path.joinpath("lineage_asset_checks")
moms_flower_shop_path = projects_path.joinpath("moms_flower_shop")
quoted_tables_path = projects_path.joinpath("quoted_tables")
