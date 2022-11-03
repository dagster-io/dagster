import pandas as pd
from dagstermill import define_dagstermill_asset
from papermill_origami.noteable_dagstermill import define_noteable_dagster_asset

from dagster import AssetIn, Field, Int, asset, file_relative_path

# TODO create an asset from a Jupyter notebook
