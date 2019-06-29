START_PIPELINE_EXECUTION_QUERY = '''
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
                        ... on MessageEvent {
                            message
                            level
                        }
                        ... on ExecutionStepStartEvent {
                            step { kind }
                        }
                        ... on ExecutionStepOutputEvent {
                            step { key kind }
                            outputName
                            typeCheck {
                                label
                                description
                                metadataEntries {
                                    label
                                    description
                                    ... on EventPathMetadataEntry {
                                        path
                                    }
                                    ... on EventJsonMetadataEntry {
                                        jsonString
                                    }
                                }
                            }
                        }
                        ... on StepExpectationResultEvent {
                            expectationResult {
                                success
                                label
                                description
                                metadataEntries {
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
                            }
                        }
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


START_PIPELINE_EXECUTION_SNAPSHOT_QUERY = '''
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
                        ... on ExecutionStepStartEvent {
                            step { kind }
                        }
                        ... on ExecutionStepOutputEvent {
                            step { key kind }
                            outputName
                            typeCheck {
                                label
                                description
                            }
                        }
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

SUBSCRIPTION_QUERY = '''
subscription subscribeTest($runId: ID!) {
    pipelineRunLogs(runId: $runId) {
        __typename
        ... on PipelineRunLogsSubscriptionSuccess {
            runId,
            messages {
                __typename
                ... on ExecutionStepOutputEvent {
                    valueRepr
                }
                ... on MessageEvent {
                    message
                    step { key solidHandleID }
                    level
                }
                ... on ExecutionStepFailureEvent {
                    error {
                        message
                        stack
                    }
                    level
                }
                ... on StepMaterializationEvent {
                    materialization {
                        label
                        description
                        metadataEntries {
                            __typename
                            label
                            description
                            ... on EventPathMetadataEntry {
                                path
                            }
                            ... on EventJsonMetadataEntry {
                                jsonString
                            }
                            ... on EventUrlMetadataEntry {
                                url
                            }
                            ... on EventTextMetadataEntry {
                                text
                            }
                        }

                    }
                }
                ... on StepExpectationResultEvent {
                    expectationResult {
                        success
                        label
                        description
                        metadataEntries {
                            label
                            description
                            ... on EventPathMetadataEntry {
                                path
                            }
                            ... on EventJsonMetadataEntry {
                                jsonString
                            }
                        }
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
