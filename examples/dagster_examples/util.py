import os

from six.moves.urllib.request import urlretrieve

from dagster import Field, OutputDefinition, String, solid


@solid(
    name='download_file',
    config_schema={
        'url': Field(String, description='The URL from which to download the file'),
        'path': Field(String, description='The path to which to download the file'),
    },
    output_defs=[
        OutputDefinition(
            String, name='path', description='The path to which the file was downloaded'
        )
    ],
    description=(
        'A simple utility solid that downloads a file from a URL to a path using '
        'urllib.urlretrieve'
    ),
)
def download_file(context):
    urlretrieve(context.solid_config['url'], context.solid_config['path'])
    return os.path.abspath(context.solid_config['path'])
