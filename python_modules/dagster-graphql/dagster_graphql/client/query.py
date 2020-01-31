STEP_EVENT_FRAGMENTS = '''
fragment eventMetadataEntryFragment on EventMetadataEntry {
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
  ... on EventMarkdownMetadataEntry {
      mdStr
  }
}


fragment stepEventFragment on StepEvent {
  step {
    key
    inputs {
      name
      type {
        key
      }
      dependsOn {
        key
      }
    }
    outputs {
      name
      type {
        key
      }
    }
    solidHandleID
    kind
    metadata {
      key
      value
    }
  }
  ... on MessageEvent {
    runId
    message
    timestamp
    level
  }
  ... on StepExpectationResultEvent {
    expectationResult {
      success
      label
      description
      metadataEntries {
        ...eventMetadataEntryFragment
      }
    }
  }
  ... on StepMaterializationEvent {
    materialization {
      label
      description
      metadataEntries {
        ...eventMetadataEntryFragment
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
        ...eventMetadataEntryFragment
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
        ...eventMetadataEntryFragment
      }
    }
  }
  ... on ExecutionStepFailureEvent {
    error {
      message
    }
    failureMetadata {
      label
      description
      metadataEntries {
        ...eventMetadataEntryFragment
      }
    }
  }
}
'''

LOG_MESSAGE_EVENT_FRAGMENT = '''
fragment logMessageEventFragment on LogMessageEvent {
  runId
  message
  timestamp
  level
  step {
    key
    inputs {
      name
      type {
        key
      }
      dependsOn {
        key
      }
    }
    outputs {
      name
      type {
        key
      }
    }
    solidHandleID
    kind
    metadata {
      key
      value
    }
  }
}
'''

START_PIPELINE_EXECUTION_RESULT_FRAGMENT = (
    '''
fragment startPipelineExecutionResultFragment on StartPipelineExecutionResult {
	__typename
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
	... on StartPipelineExecutionSuccess {
		run {
			runId
			status
			pipeline {
				name
			}
			logs {
				nodes {
					__typename
					...stepEventFragment
					...logMessageEventFragment
				}
				pageInfo {
					lastCursor
					hasNextPage
					hasPreviousPage
					count
					totalCount
				}
			}
			environmentConfigYaml
			mode
		}
	}
}
'''
    + STEP_EVENT_FRAGMENTS
    + LOG_MESSAGE_EVENT_FRAGMENT
)

START_PIPELINE_EXECUTION_MUTATION = (
    '''
mutation(
  $executionParams: ExecutionParams!
) {
  startPipelineExecution(
    executionParams: $executionParams,
  ) {
    ...startPipelineExecutionResultFragment
  }
}
'''
    + START_PIPELINE_EXECUTION_RESULT_FRAGMENT
)

START_SCHEDULED_EXECUTION_MUTATION = '''
mutation(
  $scheduleName: String!
) {
  startScheduledExecution(
    scheduleName: $scheduleName,
  ) {
    __typename
    ...on ScheduleNotFoundError {
      message
      scheduleName
    }
    ...on SchedulerNotDefinedError {
      message
    }
    ...on ScheduledExecutionBlocked {
      message
    }
    ...on PythonError {
      message
      stack
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
    ... on StartPipelineExecutionSuccess {
      run {
        runId
        status
        pipeline {
          name
        }
      }
    }
    ... on RunLauncherNotDefinedError {
      message
    }
    ... on LaunchPipelineExecutionSuccess {
      run {
        runId
        status
        pipeline {
          name
        }
      }
    }

  }
}
'''

EXECUTE_PLAN_MUTATION = (
    '''
mutation(
  $executionParams: ExecutionParams!
) {
  executePlan(
    executionParams: $executionParams,
  ) {
    __typename
    ... on InvalidStepError {
      invalidStepKey
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
    ... on ExecutePlanSuccess {
      pipeline {
        name
      }
      hasFailures
      stepEvents {
        __typename
        ...stepEventFragment
      }
    }
  }
}
'''
    + STEP_EVENT_FRAGMENTS
)

RAW_EXECUTE_PLAN_MUTATION = '''
mutation(
  $executionParams: ExecutionParams!
) {
  executePlan(
    executionParams: $executionParams,
  ) {
    __typename
    ... on InvalidStepError {
      invalidStepKey
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
    ... on ExecutePlanSuccess {
      pipeline {
        name
      }
      hasFailures
      rawEventRecords
    }
  }
}
'''

SUBSCRIPTION_QUERY = (
    STEP_EVENT_FRAGMENTS
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
                            ...eventMetadataEntryFragment
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
        }
    }
}
'''
)

LAUNCH_PIPELINE_EXECUTION_MUTATION = '''
mutation(
  $executionParams: ExecutionParams!
) {
  launchPipelineExecution(
    executionParams: $executionParams,
  ) {
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
        status
        pipeline {
          name
        }
        environmentConfigYaml
        mode
      }
    }
  }
}
'''
