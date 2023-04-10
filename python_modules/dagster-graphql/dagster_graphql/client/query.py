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

METADATA_ENTRY_FRAGMENT = """
fragment metadataEntryFragment on MetadataEntry {
  __typename
  label
  description
  ... on FloatMetadataEntry {
    floatValue
  }
  ... on IntMetadataEntry {
    intRepr
  }
  ... on BoolMetadataEntry {
    boolValue
  }
  ... on JsonMetadataEntry {
    jsonString
  }
  ... on MarkdownMetadataEntry {
    mdStr
  }
  ... on PathMetadataEntry {
    path
  }
  ... on NotebookMetadataEntry {
    path
  }
  ... on PythonArtifactMetadataEntry {
    module
    name
  }
  ... on TextMetadataEntry {
    text
  }
  ... on UrlMetadataEntry {
    url
  }
  ... on PipelineRunMetadataEntry  {
    runId
  }
  ... on AssetMetadataEntry  {
    assetKey {
      path
    }
  }
  ... on TableMetadataEntry  {
    table {
      records
      schema {
        constraints { other }
        columns {
          name
          type
          constraints { nullable unique other }
        }
      }
    }
  }
  ... on TableSchemaMetadataEntry  {
    schema {
      constraints { other }
      columns {
        name
        type
        constraints { nullable unique other }
      }
    }
  }
}
"""

STEP_EVENT_FRAGMENTS = (
    ERROR_FRAGMENT
    + METADATA_ENTRY_FRAGMENT
    + """
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
  ... on MaterializationEvent {
    label
    description
    metadataEntries {
      ...metadataEntryFragment
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
  __typename
  runId
  message
  timestamp
  level
  eventType
  ...stepEventFragment
  ... on MaterializationEvent {
    label
    description
    metadataEntries {
      __typename
      ...metadataEntryFragment
    }
  }
  ... on ExecutionStepFailureEvent {
    stepKey
    error {
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
        ...messageEventFragment
      }
      hasMorePastEvents
    }
    ... on PipelineRunLogsSubscriptionFailure {
      missingRunId
      message
    }
  }
}

"""
)

RUN_EVENTS_QUERY = (
    MESSAGE_EVENT_FRAGMENTS
    + """
query pipelineRunEvents($runId: ID!, $cursor: String) {
  logsForRun(runId: $runId, afterCursor: $cursor) {
    __typename
    ... on EventConnection {
      events {
        ...messageEventFragment
      }
      cursor
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
    ... on LaunchRunSuccess {
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
        resolvedOpSelection
      }
    }
    ... on ConflictingExecutionParamsError {
      message
    }
    ... on PresetNotFoundError {
      preset
      message
    }
    ... on RunConfigValidationInvalid {
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
mutation($executionParams: ExecutionParams, $reexecutionParams: ReexecutionParams) {
  launchPipelineReexecution(executionParams: $executionParams, reexecutionParams: $reexecutionParams) {
    __typename

    ... on PythonError {
      ...errorFragment
    }
    ... on LaunchRunSuccess {
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
    ... on RunConfigValidationInvalid {
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
