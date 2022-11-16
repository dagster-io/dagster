from dagster import asset


# placeholder so that the test works. this isn't used in the docs
@asset
def iris_dataset():
    return 1


# start
from dagstermill import define_dagstermill_asset

from dagster import AssetIn, Field, Int, file_relative_path

iris_kmeans_jupyter_notebook = define_dagstermill_asset(
    name="iris_kmeans_jupyter",
    notebook_path=file_relative_path(__file__, "./notebooks/iris-kmeans.ipynb"),
    group_name="template_tutorial",
    ins={"iris": AssetIn("iris_dataset")},
    config_schema=Field(
        Int,
        default_value=3,
        is_required=False,
        description="The number of clusters to find",
    ),
)

# end


# this is hacky so that we can test this code snippet. We need a ReconstructablePipeline to run dagstermill, and
# ReconstructablePipeline.for_module() find the jobs defined in this file. So we need to resolve all
# of the asset jobs.

from dagstermill import local_output_notebook_io_manager

from dagster import AssetSelection, define_asset_job, with_resources

assets_with_resource = with_resources(
    [iris_kmeans_jupyter_notebook, iris_dataset],
    resource_defs={
        "output_notebook_io_manager": local_output_notebook_io_manager,
    },
)
config_asset_job = define_asset_job(
    name="config_asset_job",
    selection=AssetSelection.assets(iris_kmeans_jupyter_notebook).upstream(),
).resolve(assets_with_resource, [])
