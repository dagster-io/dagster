# ruff: noqa
# We will be filling this file out as part of the PyData workshop!
import pandas as pd
from dagstermill import define_dagstermill_asset
from papermill_origami.noteable_dagstermill import define_noteable_dagster_asset

from dagster import AssetIn, Field, Int, asset, file_relative_path

# TODO 2: Uncomment the code below to create a Dagster asset of the Iris dataset
# relevant documentation - https://docs.dagster.io/concepts/assets/software-defined-assets#a-basic-software-defined-asset


# @asset(group_name="template_tutorial")
# def iris_dataset():
#     return pd.read_csv(
#         "https://archive.ics.uci.edu/ml/machine-learning-databases/iris/iris.data",
#         names=[
#             "Sepal length (cm)",
#             "Sepal width (cm)",
#             "Petal length (cm)",
#             "Petal width (cm)",
#             "Species",
#         ],
#     )


# TODO 1: Uncomment the code below to create a Dagster asset backed by a Jupyter notebook
# relevant documentation - https://docs.dagster.io/_apidocs/libraries/dagstermill#dagstermill.define_dagstermill_asset

# iris_kmeans_jupyter_notebook = define_dagstermill_asset(
#     name="iris_kmeans_jupyter",
#     notebook_path=file_relative_path(__file__, "../notebooks/iris-kmeans.ipynb"),
#     group_name="template_tutorial",
#     # ins={"iris": AssetIn("iris_dataset")},  # this code to remain commented until TODO 3
# )

# TODO 5: Uncomment the code below to create a Dagster asset backed by a Noteable notebook
# relevant documentation - https://papermill-origami.readthedocs.io/en/latest/reference/noteable_dagstermill/assets/

# notebook_id = "<your-noteable-notebook-id>"
# iris_kmeans_noteable_notebook = define_noteable_dagster_asset(
#     name="iris_kmeans_noteable",
#     notebook_id=notebook_id,
#     ins={"iris": AssetIn("iris_dataset")},
#     group_name="template_tutorial"
# )
