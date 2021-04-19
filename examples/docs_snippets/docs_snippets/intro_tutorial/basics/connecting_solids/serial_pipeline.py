# start_serial_pipeline_marker_0
import requests
import pandas
import io

from dagster import execute_pipeline, pipeline, solid


@solid
def download_cereals(_):
    response = requests.get(
        "https://raw.githubusercontent.com/dagster-io/dagster/master/examples/docs_snippets/docs_snippets/intro_tutorial/cereal.csv"
    )
    return pandas.read_csv(io.BytesIO(response.content))


@solid
def find_sugariest(context, cereals):
    sugariest_index = cereals["sugars"].argmax()
    sugariest_name = cereals["name"][sugariest_index]
    context.log.info(f"{sugariest_name} is the sugariest cereal")


@pipeline
def serial_pipeline():
    find_sugariest(download_cereals())


# end_serial_pipeline_marker_0
if __name__ == "__main__":
    result = execute_pipeline(serial_pipeline)
    assert result.success
