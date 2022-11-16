# start
from dagstermill import define_dagstermill_asset

from dagster import AssetIn, Field, Int, file_relative_path

iris_kmeans_jupyter_notebook = define_dagstermill_asset(
    name="iris_kmeans_jupyter",
    notebook_path=file_relative_path(__file__, "../notebooks/iris-kmeans.ipynb"),
    group_name="template_tutorial",
    ins={"iris": AssetIn("iris_dataset")},
    config_schema=Field(
        Int,
        default_value=3,
        is_required=False,
        description="The number of clusters to find",
    ),
)
