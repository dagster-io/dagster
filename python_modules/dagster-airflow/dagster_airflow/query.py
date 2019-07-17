# TODO need to enrich error handling as we enrich the ultimate union type for executePlan
QUERY = ''' '
mutation(
  $executionParams: ExecutionParams!
) {
  executePlan(
    executionParams: $executionParams
  ) {
    __typename
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
    ... on ExecutePlanSuccess {
      pipeline {
        name
      }
      hasFailures
      stepEvents {
        step {
          key
          kind
          solidHandleID
        }
        __typename
        ... on ExecutionStepOutputEvent {
          outputName
        }
        ... on ExecutionStepFailureEvent {
          error {
              message
          }
        }
      }
    }
    ... on InvalidStepError {
        invalidStepKey
    }
  }
}
'
'''.strip(
    '\n'
)
