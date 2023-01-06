import pandas as pd
from dagster import AssetIn, asset, file_relative_path
from dagstermill import define_dagstermill_asset
from papermill_origami.noteable_dagstermill import define_noteable_dagster_asset


# fetch the iris dataset
@asset(group_name="finished_tutorial")
def iris_dataset_finished():
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

iris_kmeans_jupyter_notebook_finished = define_dagstermill_asset(
    name="iris_kmeans_jupyter_finished",
    notebook_path=file_relative_path(__file__, "../notebooks/iris-kmeans.ipynb"),
    ins={"iris": AssetIn("iris_dataset_finished")},
    group_name="finished_tutorial",
)


# Asset backed by a Noteable notebook

notebook_id = "<your-noteable-notebook-id>"
iris_kmeans_noteable_notebook_finished = define_noteable_dagster_asset(
    name="iris_kmeans_noteable_finished",
    notebook_id=notebook_id,
    ins={"iris": AssetIn("iris_dataset_finished")},
    group_name="finished_tutorial",
)
