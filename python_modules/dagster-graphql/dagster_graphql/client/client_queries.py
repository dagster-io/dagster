CLIENT_SUBMIT_RUN_MUTATION = """
mutation($executionParams: ExecutionParams!) {
  launchRun(executionParams: $executionParams) {
    __typename

    ... on InvalidStepError {
      invalidStepKey
    }
    ... on InvalidOutputError {
      stepKey
      invalidOutputName
    }
    ... on LaunchRunSuccess {
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
    ... on RunConflict {
      message
    }
    ... on RunConfigValidationInvalid {
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

GET_RUN_STATUS_QUERY = """
query($runId: ID!) {
  runOrError(runId: $runId) {
    __typename
    ... on Run {
        status
    }
    ... on RunNotFoundError {
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
