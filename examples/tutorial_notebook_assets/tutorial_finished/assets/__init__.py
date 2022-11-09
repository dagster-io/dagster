import pandas as pd
from dagstermill import define_dagstermill_asset
from papermill_origami.noteable_dagstermill import define_noteable_dagster_asset

from dagster import AssetIn, Field, Int, asset, file_relative_path


# fetch the iris dataset
@asset(group_name="finished_tutorial")
def iris_dataset():
    return pd.read_csv(
        "https://archive.ics.uci.edu/ml/machine-learning-databases/iris/iris.data",
        names=[
            "Sepal length (cm)",
            "Sepal width (cm)",
            "Petal length (cm)",
            "Petal width (cm)",
            "Species",
        ],
    )


# Asset backed by a Jupyter notebook

iris_kmeans_jupyter_notebook = define_dagstermill_asset(
    name="iris_kmeans_jupyter",
    notebook_path=file_relative_path(__file__, "../notebooks/iris-kmeans.ipynb"),
    ins={"iris": AssetIn("iris_dataset")},
    group_name="finished_tutorial",
)


# Asset backed by a Noteable notebook

notebook_id = "<your-noteable-notebook-id>"
iris_kmeans_noteable_notebook = define_noteable_dagster_asset(
    name="iris_kmeans_noteable",
    notebook_id=notebook_id,
    ins={"iris": AssetIn("iris_dataset")},
    group_name="finished_tutorial",
)
