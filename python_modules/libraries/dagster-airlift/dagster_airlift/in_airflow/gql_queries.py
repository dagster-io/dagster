VERIFICATION_QUERY = """
query VerificationQuery {
    version
}
"""

ASSET_NODES_QUERY = """
query AssetNodeQuery {
    assetNodes {
        id
        assetKey {
            path
        }
        metadataEntries {
            ... on TextMetadataEntry {
                label
                text
            }
            ... on JsonMetadataEntry {
                label
                jsonString
            }
            __typename
        }
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
        isPartitioned
        partitionDefinition {
          type
          name
          fmt
        }
        partitionKeys
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
      tags {
        key
        value
      }
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

RUNS_BY_TAG_QUERY = """
query RunsByTagQuery($filter: RunsFilter!) {
  runsOrError(filter: $filter) {
    ... on Runs {
      results {
        id
        status
        tags {
          key
          value
        }
      }
    }
  }
}
"""
