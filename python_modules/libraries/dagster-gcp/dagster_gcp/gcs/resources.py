from google.cloud import storage

from dagster import Field, Noneable, StringSource, resource


@resource(
    {'project': Field(Noneable(StringSource), is_required=False, description='Project name',)},
    description='This resource provides a GCS client',
)
def gcs_resource(init_context):
    return storage.client.Client(**init_context.resource_config)
