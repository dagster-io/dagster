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

STEP_EVENT_FRAGMENTS = (
    ERROR_FRAGMENT
    + """
fragment metadataEntryFragment on EventMetadataEntry {
  __typename
  label
  description
  ... on EventFloatMetadataEntry {
    floatValue
  }
  ... on EventIntMetadataEntry {
    intRepr
  }
  ... on EventJsonMetadataEntry {
    jsonString
  }
  ... on EventMarkdownMetadataEntry {
    mdStr
  }
  ... on EventPathMetadataEntry {
    path
  }
  ... on EventPythonArtifactMetadataEntry {
    module
    name
  }
  ... on EventTextMetadataEntry {
    text
  }
  ... on EventUrlMetadataEntry {
    url
  }
}

fragment stepEventFragment on StepEvent {
  stepKey
  solidHandleID
  ... on EngineEvent {
    metadataEntries {
      ...metadataEntryFragment
    }
    markerStart
    markerEnd
    engineError: error {
      ...errorFragment
    }
  }
  ... on ExecutionStepFailureEvent {
    error {
      ...errorFragment
    }
    failureMetadata {
      label
      description
      metadataEntries {
        ...metadataEntryFragment
      }
    }
  }
  ... on ExecutionStepInputEvent {
    inputName
    typeCheck {
      __typename
      success
      label
      description
      metadataEntries {
        ...metadataEntryFragment
      }
    }
  }
  ... on ExecutionStepOutputEvent {
    outputName
    typeCheck {
      __typename
      success
      label
      description
      metadataEntries {
        ...metadataEntryFragment
      }
    }
    metadataEntries {
      ...metadataEntryFragment
    }
  }

  ... on ExecutionStepUpForRetryEvent {
    retryError: error {
      ...errorFragment
    }
    secondsToWait
  }

  ... on ObjectStoreOperationEvent {
        stepKey
        operationResult {
            op
            metadataEntries {
                ...metadataEntryFragment
            }
        }
    }

  ... on StepExpectationResultEvent {
    expectationResult {
      success
      label
      description
      metadataEntries {
        ...metadataEntryFragment
      }
    }
  }
  ... on StepMaterializationEvent {
    materialization {
      label
      description
      metadataEntries {
        ...metadataEntryFragment
      }
    }
  }

  ... on MessageEvent {
    runId
    message
    timestamp
    level
    eventType
  }



}
"""
)

MESSAGE_EVENT_FRAGMENTS = (
    """
fragment messageEventFragment on MessageEvent {
  runId
  message
  timestamp
  level
  eventType
  ...stepEventFragment
  ... on PipelineInitFailureEvent {
    initError: error {
      ...errorFragment
    }
  }
}
"""
    + STEP_EVENT_FRAGMENTS
)


SUBSCRIPTION_QUERY = (
    MESSAGE_EVENT_FRAGMENTS
    + """
subscription subscribeTest($runId: ID!) {
  pipelineRunLogs(runId: $runId) {
    __typename
    ... on PipelineRunLogsSubscriptionSuccess {
      run {
        runId
      }
      messages {
        __typename
        ...messageEventFragment

        # only include here because unstable between runs
        ... on StepMaterializationEvent {
          materialization {
            label
            description
            metadataEntries {
              __typename
              ...metadataEntryFragment
            }
          }
        }

        ... on ExecutionStepFailureEvent {
          stepKey
          error {
            ...errorFragment
          }
        }
      }
    }

    ... on PipelineRunLogsSubscriptionFailure {
      missingRunId
      message
    }
  }
}

"""
)

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


LAUNCH_PIPELINE_REEXECUTION_MUTATION = (
    ERROR_FRAGMENT
    + """
mutation($executionParams: ExecutionParams!) {
  launchPipelineReexecution(executionParams: $executionParams) {
    __typename

    ... on PythonError {
      ...errorFragment
    }
    ... on LaunchPipelineRunSuccess {
      run {
        runId
        status
        pipeline {
          name
        }
        tags {
          key
          value
        }
        runConfigYaml
        mode
        rootRunId
        parentRunId
      }
    }
    ... on PipelineNotFoundError {
      message
      pipelineName
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
    ... on InvalidStepError {
      invalidStepKey
    }
    ... on InvalidOutputError {
      stepKey
      invalidOutputName
    }
    ... on ConflictingExecutionParamsError {
      message
    }
    ... on PresetNotFoundError {
      preset
      message
    }
  }
}
"""
)

PIPELINE_REEXECUTION_INFO_QUERY = """
query ReexecutionInfoQuery($runId: ID!) {
  pipelineRunOrError(runId: $runId) {
    __typename
    ... on PipelineRun {
        stepKeysToExecute
      }
    }
  }
"""

LAUNCH_PARTITION_BACKFILL_MUTATION = (
    ERROR_FRAGMENT
    + """
mutation($backfillParams: LaunchBackfillParams!) {
  launchPartitionBackfill(backfillParams: $backfillParams) {
    __typename
    ... on PythonError {
      ...errorFragment
    }
    ... on PartitionSetNotFoundError {
      message
    }
    ... on LaunchBackfillSuccess {
      backfillId
      launchedRunIds
    }
  }
}
"""
)
