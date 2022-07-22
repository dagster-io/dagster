from dagster.utils import script_relative_path

# isort: split
# start

from urllib.request import urlretrieve

from dagster import Field, OutputDefinition, String, op


@op(
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
        "A simple utility op that downloads a file from a URL to a path using urllib.urlretrieve"
    ),
)
def download_file(context):
    output_path = script_relative_path(context.op_config["path"])
    urlretrieve(context.op_config["url"], output_path)
    return output_path
