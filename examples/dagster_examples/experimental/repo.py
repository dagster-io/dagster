# pylint: disable=no-value-for-parameter

from dagster import PresetDefinition, RepositoryDefinition, pipeline, solid


@solid
def save_metrics(context, data_path):
    context.log.info("Saving metrics to path {data_path}".format(data_path=data_path))


@pipeline(
    preset_defs=[
        PresetDefinition(
            name="test",
            environment_dict={
                "solids": {
                    "save_metrics": {
                        "inputs": {"data_path": {"value": "s3://bucket-name/test_data"}}
                    }
                }
            },
        ),
    ],
)
def metrics_pipeline():
    save_metrics()


@solid
def rollup_data(context, data_path):
    context.log.info("Rolling up data from path {data_path}".format(data_path=data_path))


@pipeline(
    preset_defs=[
        PresetDefinition(
            name="test",
            environment_dict={
                "solids": {
                    "rollup_data": {
                        "inputs": {"data_path": {"value": "s3://bucket-name/test_data"}}
                    }
                }
            },
        ),
    ],
)
def rollup_pipeline():
    rollup_data()


def define_repo():
    return RepositoryDefinition(
        name='experimental_repository', pipeline_defs=[metrics_pipeline, rollup_pipeline]
    )
