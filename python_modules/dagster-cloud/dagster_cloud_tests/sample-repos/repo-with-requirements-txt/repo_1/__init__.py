from dagster import Definitions, load_assets_from_modules

from repo_1 import assets

defs = Definitions(assets=load_assets_from_modules([assets]))
