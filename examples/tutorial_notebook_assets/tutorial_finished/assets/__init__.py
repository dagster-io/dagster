import pandas as pd
from dagster import AssetIn, asset, file_relative_path
from dagstermill import define_dagstermill_asset


# fetch the iris dataset
@asset(group_name="finished_tutorial")
def iris_dataset_finished():
    return pd.read_csv(
        "https://docs.dagster.io/assets/iris.csv",
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
