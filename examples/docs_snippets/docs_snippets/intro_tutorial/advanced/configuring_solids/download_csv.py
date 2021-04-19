import requests
import pandas
import io
from dagster import solid

# start_download_cereals_marker
@solid
def download_cereals(_):
    response = requests.get(
        "https://raw.githubusercontent.com/dagster-io/dagster/master/examples/docs_snippets/docs_snippets/intro_tutorial/cereal.csv"
    )
    return pandas.read_csv(io.BytesIO(response.content))


# end_download_cereals_marker


# start_download_csv_marker
@solid(config_schema={"url": str})
def download_csv(context):
    response = requests.get(context.solid_config["url"])
    return pandas.read_csv(io.BytesIO(response.content))


# end_download_csv_marker
