ASSET_NODES_QUERY = """
query AssetNodeQuery {
    assetNodes {
        id
        assetKey {
            path
        }
        opName
        jobs {
            id
            name
            repository {
                id
                name
                location {
                    id
                    name
                }
            }
        }
    }
}
"""

TRIGGER_ASSETS_MUTATION = """
mutation LaunchAssetsExecution($executionParams: ExecutionParams!) {
  launchPipelineExecution(executionParams: $executionParams) {
    ... on LaunchRunSuccess {
      run {
        id
        pipelineName
        __typename
      }
      __typename
    }
    ... on PipelineNotFoundError {
      message
      __typename
    }
    ... on InvalidSubsetError {
      message
      __typename
    }
    ... on RunConfigValidationInvalid {
      errors {
        message
        __typename
      }
      __typename
    }
    ...PythonErrorFragment
    __typename
  }
}

fragment PythonErrorFragment on PythonError {
  message
  stack
  errorChain {
    ...PythonErrorChain
    __typename
  }
  __typename
}

fragment PythonErrorChain on ErrorChainLink {
  isExplicitLink
  error {
    message
    stack
    __typename
  }
  __typename
}
"""

RUNS_QUERY = """
query RunQuery($runId: ID!) {
	runOrError(runId: $runId) {
		__typename
		...PythonErrorFragment
		...NotFoundFragment
		... on Run {
			id
			status
			__typename
		}
	}
}
fragment NotFoundFragment on RunNotFoundError {
	__typename
	message
}
fragment PythonErrorFragment on PythonError {
	__typename
	message
	stack
	causes {
		message
		stack
		__typename
	}
}
"""
