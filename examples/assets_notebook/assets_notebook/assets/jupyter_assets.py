import json
import os

import dagstermill as dm
import numpy as np
import pandas as pd
import requests
from pandas import DataFrame
from papermill_origami.noteable_dagstermill import define_noteable_dagster_asset
from sklearn import datasets

from dagster import AssetIn, AssetKey, Field, Int, asset, graph, repository

from .data_assets import iris_dataset

############# Jupyter Notebook #############
notebook_id = "c38b1d2b-53b7-428f-801b-c465e8f84255"  # iris-kmeans
jupyter_iris_notebook = define_noteable_dagster_asset(
    name="iris_notebook",
    notebook_id=notebook_id,
    config_schema=Field(
        Int,
        default_value=3,
        is_required=False,
        description="The number of clusters to use in the K-Means algorithm",
    ),
    ins={
        "iris": AssetIn(key=AssetKey("iris_dataset")),
    },
)
# jupyter_asset = dm.define_dagstermill_asset
# fill in the rest of this once the PR merges
