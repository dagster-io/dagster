from papermill_origami.noteable_dagstermill import define_noteable_dagstermill_op
from dagster import op, job, In, Field, Int, define_asset_job, Out, fs_io_manager, repository, AssetIn, with_resources, asset
import dagstermill as dm

import pandas as pd
import numpy as np
from sklearn import datasets
from pandas import DataFrame
from .assets import ping_integration
from .utils import define_noteable_dagster_asset

# op, a Dagster concept, is a user defined computation function. An op performs a computation task within a job or graph.
@op(out={"iris": Out(dagster_type=DataFrame, io_manager_key="fs_io_manager")})
def iris():
    sk_iris = datasets.load_iris()
    return pd.DataFrame(
        data=np.c_[sk_iris["data"], sk_iris["target"]],
        columns=sk_iris["feature_names"] + ["target"],
    )


# iris_asset_job = define_asset_job(name="iris_job", selection="iris")

notebook_id = "c38b1d2b-53b7-428f-801b-c465e8f84255" # iris-kmeans_3
# version_id = "3b74b26c-202b-43d3-aa7d-3a33f6d8f9d5"
demo = define_noteable_dagstermill_op(
    "demo",
    notebook_path=f"noteable://{notebook_id}",
    output_notebook_name="demo_output",  # Can be populated automatically to the run of the input path
    config_schema=Field(
        Int,
        default_value=3,
        is_required=False,
        description="The number of clusters to use in the K-Means algorithm",
    ),
    ins={"iris": In(dagster_type=DataFrame, input_manager_key="fs_io_manager")},
)
# output notebook name - dagster mill ops will return an output with that name that is the notebook object (buffered io base)


@job(
    resource_defs={
        "output_notebook_io_manager": dm.local_output_notebook_io_manager,
        "fs_io_manager": fs_io_manager,
    }
)
def run_demo():
    demo(iris())


@asset
def iris_asset():
    sk_iris = datasets.load_iris()
    return pd.DataFrame(
        data=np.c_[sk_iris["data"], sk_iris["target"]],
        columns=sk_iris["feature_names"] + ["target"],
    )

noteable_asset = define_noteable_dagster_asset(
    name="iris_notebook",
    notebook_path=f"noteable://{notebook_id}",
    notebook_url=f"https://app.noteable.io/f/{notebook_id}",
    config_schema=Field(
        Int,
        default_value=3,
        is_required=False,
        description="The number of clusters to use in the K-Means algorithm",
    ),
    ins={"iris": AssetIn(key="iris_asset", dagster_type=DataFrame, input_manager_key="fs_io_manager")},
)


@asset
def my_asset():
    return 1

@asset(
    ins={"an_in": AssetIn("my_asset")}
)
def second_asset(**assets):
    print(assets)



@repository
def noteable_repo():
    return [
        run_demo,
        ping_integration,
        with_resources([noteable_asset, iris_asset],
            resource_defs={
            "output_notebook_io_manager": dm.local_output_notebook_io_manager,
            "fs_io_manager": fs_io_manager,
          }
        )
    ]