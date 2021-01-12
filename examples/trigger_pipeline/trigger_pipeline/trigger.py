from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport

# start_trigger_marker_1
ERROR_FRAGMENT = """
fragment errorFragment on PythonError {
  message
  className
  stack
  cause {
    message
    className
    stack
    cause {
      message
      className
      stack
    }
  }
}
"""

LAUNCH_PIPELINE_EXECUTION_MUTATION = (
    ERROR_FRAGMENT
    + """
mutation($executionParams: ExecutionParams!) {
  launchPipelineExecution(executionParams: $executionParams) {
    __typename

    ... on InvalidStepError {
      invalidStepKey
    }
    ... on InvalidOutputError {
      stepKey
      invalidOutputName
    }
    ... on LaunchPipelineRunSuccess {
      run {
        runId
        pipeline {
          name
        }
        tags {
          key
          value
        }
        status
        runConfigYaml
        mode
      }
    }
    ... on ConflictingExecutionParamsError {
      message
    }
    ... on PresetNotFoundError {
      preset
      message
    }
    ... on PipelineConfigValidationInvalid {
      pipelineName
      errors {
        __typename
        message
        path
        reason
      }
    }
    ... on PipelineNotFoundError {
      message
      pipelineName
    }
    ... on PythonError {
      ...errorFragment
    }
  }
}
"""
)
# end_trigger_marker_1

# start_trigger_marker_4
REPOSITORY_LOCATION_FROM_MODULE = "repo"
# end_trigger_marker_4

# start_trigger_marker_2
REPOSITORY_LOCATION_FROM_FILE = "repo.py"
REPOSITORY_NAME = "my_repo"
PIPELINE_NAME = "do_math"
RUN_CONFIG = {"solids": {"add_one": {"inputs": {"num": 5}}, "add_two": {"inputs": {"num": 6}}}}
MODE = "default"

# end_trigger_marker_2

# start_trigger_marker_0 # start_trigger_marker_3
def launch_pipeline_over_graphql(
    location, repo_name, pipeline_name, run_config, mode, url="http://localhost:3000/graphql"
):
    transport = RequestsHTTPTransport(url=url)
    client = Client(transport=transport, fetch_schema_from_transport=True)
    # end_trigger_marker_0

    query = LAUNCH_PIPELINE_EXECUTION_MUTATION
    params = {
        "executionParams": {
            "selector": {
                "repositoryLocationName": location,
                "repositoryName": repo_name,
                "pipelineName": pipeline_name,
            },
            "runConfigData": run_config,
            "mode": mode,
        }
    }
    return client.execute(gql(query), variable_values=params)


if __name__ == "__main__":

    result = launch_pipeline_over_graphql(
        location=REPOSITORY_LOCATION_FROM_FILE,
        repo_name=REPOSITORY_NAME,
        pipeline_name=PIPELINE_NAME,
        run_config=RUN_CONFIG,
        mode=MODE,
    )
# end_trigger_marker_3
