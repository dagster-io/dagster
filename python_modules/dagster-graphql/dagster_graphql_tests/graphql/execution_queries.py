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
        ... on RunLauncherNotDefinedError {
            message
        }
        ... on InvalidStepError {
            invalidStepKey
        }
        ... on InvalidOutputError {
            stepKey
            invalidOutputName
        }
        ... on PipelineConfigValidationInvalid {
            pipeline {
                name
            }
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
        ... on LaunchPipelineExecutionSuccess {
            run {
                runId
                pipeline {
                    ... on PipelineReference {
                        name
                    }
                }
                logs {
                    nodes {
                        __typename
                        ... on MessageEvent {
                            message
                            level
                        }
                        ...stepEventFragment
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

START_PIPELINE_EXECUTION_RESULT_FRAGMENT = '''
    fragment startPipelineExecutionResultFragment on StartPipelineExecutionResult {
        __typename
        ... on StartPipelineExecutionSuccess {
            run {
                runId
                pipeline { ...on PipelineReference { name } }
                logs {
                    nodes {
                        __typename
                        ... on MessageEvent  {
                            message
                            level
                        }
                        ...stepEventFragment
                    }
                }
                tags {
                    key
                    value
                }
            }
        }
        ... on PipelineConfigValidationInvalid {
            pipeline { name }
            errors { message }
        }
        ... on PipelineNotFoundError {
            pipelineName
        }
        ... on PythonError {
            message
        }
    }
'''

START_PIPELINE_EXECUTION_QUERY = (
    FRAGMENTS
    + START_PIPELINE_EXECUTION_RESULT_FRAGMENT
    + '''

mutation (
    $executionParams: ExecutionParams!
) {
    startPipelineExecution(
        executionParams: $executionParams
    ) {
        ...startPipelineExecutionResultFragment
    }
}
'''
)

START_SCHEDULED_EXECUTION_QUERY = (
    FRAGMENTS
    + START_PIPELINE_EXECUTION_RESULT_FRAGMENT
    + LAUNCH_PIPELINE_EXECUTION_RESULT_FRAGMENT
    + '''

mutation (
    $scheduleName: String!
) {
    startScheduledExecution(
        scheduleName: $scheduleName
    ) {
        ...on ScheduleNotFoundError {
            message
            scheduleName
        }
        ...on SchedulerNotDefinedError {
            message
        }
        ...on ScheduledExecutionBlocked {
            __typename
            message
        }
        ...startPipelineExecutionResultFragment
        ...launchPipelineExecutionResultFragment
    }
}
'''
)


START_PIPELINE_EXECUTION_SNAPSHOT_QUERY = (
    FRAGMENTS
    + '''
mutation (
    $executionParams: ExecutionParams!
) {
    startPipelineExecution(
        executionParams: $executionParams
    ) {
        __typename
        ... on StartPipelineExecutionSuccess {
            run {
                pipeline { ...on PipelineReference { name } }
                logs {
                    nodes {
                        __typename
                        ... on MessageEvent {
                            level
                        }
                        ...stepEventFragment
                    }
                }
                tags {
                    key
                    value
                }
            }
        }
        ... on PipelineConfigValidationInvalid {
            pipeline { name }
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
)

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
