from dagster_aws.emr import emr_pyspark_step_launcher
from dagster_aws.s3 import s3_plus_default_storage_defs, s3_resource
from dagster_pyspark import pyspark_resource

from dagster import ModeDefinition, PresetDefinition, RepositoryDefinition, pipeline, solid

mode = ModeDefinition(
    name='prod',
    resource_defs={
        'pyspark_step_launcher': emr_pyspark_step_launcher,
        'pyspark': pyspark_resource,
        's3': s3_resource,
    },
    system_storage_defs=s3_plus_default_storage_defs,
)

preset = PresetDefinition.from_files(
    name='prod', mode='prod', environment_files=['prod_resources.yaml', 's3_storage.yaml'],
)


@solid(required_resource_keys={'pyspark_step_launcher'})
def hello(_):
    return 1


@pipeline(
    mode_defs=[mode], preset_defs=[preset],
)
def my_pipeline():
    hello()


def define_repository():
    return RepositoryDefinition('emr_pyspark', pipeline_defs=[my_pipeline])
