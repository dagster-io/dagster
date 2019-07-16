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
}

fragment stepEventFragment on StepEvent {
    ... on ExecutionStepStartEvent {
        step { kind }
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
}

'''
START_PIPELINE_EXECUTION_QUERY = (
    FRAGMENTS
    + '''

mutation (
    $executionParams: ExecutionParams!
    $reexecutionConfig: ReexecutionConfig
) {
    startPipelineExecution(
        executionParams: $executionParams
        reexecutionConfig: $reexecutionConfig
    ) {
        __typename
        ... on StartPipelineExecutionSuccess {
            run {
                runId
                pipeline { name }
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
            }
        }
        ... on PipelineConfigValidationInvalid {
            pipeline { name }
            errors { message }
        }
        ... on PipelineNotFoundError {
            pipelineName
        }
    }
}
'''
)


START_PIPELINE_EXECUTION_SNAPSHOT_QUERY = (
    FRAGMENTS
    + '''
mutation (
    $executionParams: ExecutionParams!
    $reexecutionConfig: ReexecutionConfig
) {
    startPipelineExecution(
        executionParams: $executionParams
        reexecutionConfig: $reexecutionConfig
    ) {
        __typename
        ... on StartPipelineExecutionSuccess {
            run {
                pipeline { name }
                logs {
                    nodes {
                        __typename
                        ... on MessageEvent {
                            level
                        }
                        ...stepEventFragment
                    }
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
            runId,
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
        ... on PipelineRunLogsSubscriptionMissingRunIdFailure {
            missingRunId
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
