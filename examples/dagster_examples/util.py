import os

from dagster import Field, OutputDefinition, Path, solid, String
from dagster.seven import urlretrieve


@solid(
    name='download_file',
    config={
        'url': Field(String, description='The URL from which to download the file'),
        'path': Field(Path, description='The path to which to download the file'),
    },
    output_defs=[
        OutputDefinition(Path, name='path', description='The path to which the file was downloaded')
    ],
    description=(
        'A simple utility solid that downloads a file from a URL to a path using '
        'urllib.urlretrieve'
    ),
)
def download_file(context):
    urlretrieve(context.solid_config['url'], context.solid_config['path'])
    return os.path.abspath(context.solid_config['path'])
