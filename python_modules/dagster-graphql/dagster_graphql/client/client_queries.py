CLIENT_SUBMIT_PIPELINE_RUN_MUTATION = """
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
      }
    }
    ... on ConflictingExecutionParamsError {
      message
    }
    ... on PresetNotFoundError {
      message
    }
    ... on PipelineRunConflict {
      message
    }
    ... on PipelineConfigValidationInvalid {
      errors {
        __typename
        message
        path
        reason
      }
    }
    ... on PipelineNotFoundError {
      message
    }
    ... on PythonError {
      message
    }
  }
}
"""

CLIENT_GET_REPO_LOCATIONS_NAMES_AND_PIPELINES_QUERY = """
query {
  repositoriesOrError {
    __typename
    ... on RepositoryConnection {
      nodes {
        name
        location {
          name
        }
        pipelines {
          name
        }
      }
    }
    ... on PythonError {
      message
    }
  }
}
"""

RELOAD_REPOSITORY_LOCATION_MUTATION = """
mutation ($repositoryLocationName: String!) {
   reloadRepositoryLocation(repositoryLocationName: $repositoryLocationName) {
      __typename
      ... on WorkspaceLocationEntry {
        name
        locationOrLoadError {
          __typename
          ... on RepositoryLocation {
            isReloadSupported
            repositories {
                name
            }
          }
          ... on PythonError {
            message
          }
        }
      }
      ... on ReloadNotSupported {
        message
      }
      ... on RepositoryLocationNotFound {
        message
      }
   }
}
"""

GET_PIPELINE_RUN_STATUS_QUERY = """
query($runId: ID!) {
  pipelineRunOrError(runId: $runId) {
    __typename
    ... on PipelineRun {
        status
    }
    ... on PipelineRunNotFoundError {
      message
    }
    ... on PythonError {
      message
    }
  }
}
"""

SHUTDOWN_REPOSITORY_LOCATION_MUTATION = """
mutation ($repositoryLocationName: String!) {
   shutdownRepositoryLocation(repositoryLocationName: $repositoryLocationName) {
      __typename
      ... on PythonError {
        message
      }
      ... on RepositoryLocationNotFound {
        message
      }
   }
}
"""

TERMINATE_RUN_JOB_MUTATION = """
mutation TerminateRun($runId: String!) {
  terminateRun(runId: $runId){
    __typename
    ... on TerminateRunSuccess{
      run {
        runId
      }
    }
    ... on TerminateRunFailure {
      message
    }
    ... on RunNotFoundError {
      runId
    }
    ... on PythonError {
      message
      stack
    }
  }
}
"""
