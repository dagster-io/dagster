FRAGMENTS = '''
fragment metadataEntryFragment on EventMetadataEntry {
    label
    description
    ... on EventPathMetadataEntry {
        path
    }
    ... on EventJsonMetadataEntry {
        jsonString
    }
    ... on EventTextMetadataEntry {
        text
    }
    ... on EventUrlMetadataEntry {
        url
    }
    ... on EventPythonArtifactMetadataEntry {
        module
        name
    }
    ... on EventFloatMetadataEntry {
        value
    }
}

fragment stepEventFragment on StepEvent {
    ... on ExecutionStepStartEvent {
        step { key kind }
    }
    ... on ExecutionStepSuccessEvent {
        step { key }
    }
    ... on ExecutionStepFailureEvent {
        step { key kind }
        error {
            message
        }
        failureMetadata {
            label
            description
            metadataEntries {
                ...metadataEntryFragment
            }
        }
    }
    ... on ExecutionStepSkippedEvent {
        step { key }
    }
    ... on ExecutionStepInputEvent {
        step { key kind }
        inputName
        typeCheck {
            label
            description
            metadataEntries {
                ...metadataEntryFragment
            }
        }
    }
    ... on ExecutionStepOutputEvent {
        step { key kind }
        outputName
        typeCheck {
            label
            description
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
    ... on ObjectStoreOperationEvent {
        step { key }
        operationResult {
            op
            metadataEntries {
                ...metadataEntryFragment
            }
        }
    }
}
'''

LAUNCH_PIPELINE_EXECUTION_RESULT_FRAGMENT = '''
    fragment launchPipelineExecutionResultFragment on LaunchPipelineExecutionResult {
        __typename
        ... on InvalidStepError {
            invalidStepKey
        }
        ... on InvalidOutputError {
            stepKey
            invalidOutputName
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
            message
            stack
            cause {
                message
                stack
            }
        }
        ... on LaunchPipelineRunSuccess {
            run {
                runId
                pipeline {
                    ... on PipelineReference {
                        name
                    }
                }
                tags {
                    key
                    value
                }
            }
        }
    }
'''

LAUNCH_PIPELINE_EXECUTION_RESULT_FRAGMENT = '''
    fragment launchPipelineExecutionResultFragment on LaunchPipelineExecutionResult {
        __typename
        ... on LaunchPipelineRunSuccess {
            run {
                runId
                pipeline { ...on PipelineReference { name } }
                tags {
                    key
                    value
                }
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
            errors { message }
        }
        ... on PipelineNotFoundError {
            pipelineName
        }
        ... on PythonError {
            message
            stack
            cause {
                message
                stack
            }
        }
    }
'''


EXECUTE_RUN_IN_PROCESS_RESULT_FRAGMENT = '''
    fragment executeRunInProcessResultFragment on ExecuteRunInProcessResult {
        __typename
        ... on ExecuteRunInProcessSuccess {
            run {
                runId
                pipeline { ...on PipelineReference { name } }
                tags {
                    key
                    value
                }
            }
        }
        ... on PipelineConfigValidationInvalid {
            pipelineName
            errors { message }
        }
        ... on PipelineNotFoundError {
            pipelineName
        }
        ... on PythonError {
            message
            stack
            cause {
                message
                stack
            }
        }
        ... on PipelineRunNotFoundError {
            message
        }
    }
'''

LAUNCH_PIPELINE_REEXECUTION_RESULT_FRAGMENT = '''
    fragment launchPipelineReexecutionResultFragment on LaunchPipelineReexecutionResult {
        __typename
        ... on LaunchPipelineRunSuccess {
            run {
                runId
                pipeline { ...on PipelineReference { name } }
                tags {
                    key
                    value
                }
            }
        }
        ... on PipelineConfigValidationInvalid {
            pipelineName
            errors { message }
        }
         ... on ConflictingExecutionParamsError {
            message
        }
        ... on PresetNotFoundError {
            preset
            message
        }
        ... on PipelineNotFoundError {
            pipelineName
        }
        ... on PythonError {
            message
            stack
            cause {
                message
                stack
            }
        }
    }
'''

LAUNCH_PIPELINE_EXECUTION_QUERY = (
    LAUNCH_PIPELINE_EXECUTION_RESULT_FRAGMENT
    + '''

mutation (
    $executionParams: ExecutionParams!
) {
    launchPipelineExecution(
        executionParams: $executionParams
    ) {
        ...launchPipelineExecutionResultFragment
    }
}
'''
)

EXECUTE_RUN_IN_PROCESS_QUERY = (
    EXECUTE_RUN_IN_PROCESS_RESULT_FRAGMENT
    + '''

mutation (
    $repositoryLocationName: String!
    $repositoryName: String!
    $runId: String!
) {
    executeRunInProcess(
        repositoryLocationName: $repositoryLocationName
        repositoryName: $repositoryName
        runId: $runId
    ) {
        ...executeRunInProcessResultFragment
    }
}
'''
)


LAUNCH_PIPELINE_REEXECUTION_QUERY = (
    LAUNCH_PIPELINE_REEXECUTION_RESULT_FRAGMENT
    + '''

mutation (
    $executionParams: ExecutionParams!
) {
    launchPipelineReexecution(
        executionParams: $executionParams
    ) {
        ...launchPipelineReexecutionResultFragment
    }
}
'''
)


LAUNCH_PIPELINE_REEXECUTION_SNAPSHOT_QUERY = '''
mutation (
    $executionParams: ExecutionParams!
) {
    launchPipelineReexecution(
        executionParams: $executionParams
    ) {
        __typename
        ... on LaunchPipelineRunSuccess {
            run {
                pipeline { ...on PipelineReference { name } }
                tags {
                    key
                    value
                }
                rootRunId
                parentRunId
            }
        }
        ... on PipelineConfigValidationInvalid {
            pipelineName
            errors { message }
        }
        ... on PipelineNotFoundError {
            pipelineName
        }
        ... on InvalidStepError {
            invalidStepKey
        }
        ... on InvalidOutputError {
            stepKey
            invalidOutputName
        }
    }
}
'''
LAUNCH_PIPELINE_EXECUTION_SNAPSHOT_FRIENDLY = '''
mutation(
  $executionParams: ExecutionParams!
) {
  launchPipelineExecution(
    executionParams: $executionParams,
  ) {
    __typename
    ... on InvalidStepError {
      invalidStepKey
    }
    ... on InvalidOutputError {
      stepKey
      invalidOutputName
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
      message
      stack
    }
    ... on LaunchPipelineRunSuccess {
      run {
        status
        pipeline {
          name
        }
        mode
      }
    }
  }
}
'''
SUBSCRIPTION_QUERY = (
    FRAGMENTS
    + '''
subscription subscribeTest($runId: ID!) {
    pipelineRunLogs(runId: $runId) {
        __typename
        ... on PipelineRunLogsSubscriptionSuccess {
            run {
                runId
            },
            messages {
                __typename
                ...stepEventFragment

                ... on MessageEvent {
                    message
                    step { key solidHandleID }
                    level
                }

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
                    step { key kind }
                    error {
                        message
                        stack
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
'''
)


PIPELINE_REEXECUTION_INFO_QUERY = '''
query ReexecutionInfoQuery($runId: ID!) {
  pipelineRunOrError(runId: $runId) {
    __typename
    ... on PipelineRun {
        stepKeysToExecute
      }
    }
  }
'''
