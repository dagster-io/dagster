from papermill_origami.noteable_dagstermill import define_noteable_dagster_asset

from dagster import AssetIn, AssetKey, Field, Int

notebook_id = "c38b1d2b-53b7-428f-801b-c465e8f84255"  # TODO remove and uncomment the line below
# notebook_id = "your-notebook-id-here"
noteable_iris_notebook = define_noteable_dagster_asset(
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
