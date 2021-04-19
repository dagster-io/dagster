"""isort:skip_file"""

# start_solid_marker
import requests
import pandas
import io
from dagster import pipeline, solid


@solid
def hello_cereal(context):
    response = requests.get(
        "https://raw.githubusercontent.com/dagster-io/dagster/master/examples/docs_snippets/docs_snippets/intro_tutorial/cereal.csv"
    )
    dataframe = pandas.read_csv(io.BytesIO(response.content))
    context.log.info(f"Found {len(dataframe)} cereals")


# end_solid_marker


# start_pipeline_marker
@pipeline
def hello_cereal_pipeline():
    hello_cereal()


# end_pipeline_marker

# start_execute_marker
from dagster import execute_pipeline

if __name__ == "__main__":
    result = execute_pipeline(hello_cereal_pipeline)

# end_execute_marker
