from six.moves.urllib.request import urlretrieve

from dagster import Field, OutputDefinition, String, solid
from dagster.utils import script_relative_path


@solid(
    name="download_file",
    config_schema={
        "url": Field(String, description="The URL from which to download the file"),
        "path": Field(String, description="The path to which to download the file"),
    },
    output_defs=[
        OutputDefinition(
            String, name="path", description="The path to which the file was downloaded"
        )
    ],
    description=(
        "A simple utility solid that downloads a file from a URL to a path using "
        "urllib.urlretrieve"
    ),
)
def download_file(context):
    output_path = script_relative_path(context.solid_config["path"])
    urlretrieve(context.solid_config["url"], output_path)
    return output_path
