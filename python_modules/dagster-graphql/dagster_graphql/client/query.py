START_PIPELINE_EXECUTION_QUERY = '''
mutation(
  $executionParams: ExecutionParams!
) {
  startPipelineExecution(
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
}


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
