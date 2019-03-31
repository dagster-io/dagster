from dagster import solid, Dict, Field, OutputDefinition, Path

from .types import FileExistsAtPath


@solid(
    name='download_from_s3',
    config_field=Field(
        Dict(
            fields={
                'target_file': Field(
                    Path, description=('Specifies the path at which to download the object.')
                )
            }
        )
    ),
    description='Downloads an object from S3.',
    outputs=[OutputDefinition(FileExistsAtPath, description='The path to the downloaded object.')],
)
def download_from_s3(context):
    target_file = context.solid_config['target_file']
    return context.resources.download_manager.download_file(context, target_file)

