# TODO need to enrich error handling as we enrich the ultimate union type for executePlan
QUERY_TEMPLATE = '''
mutation(
  $executionParams: ExecutionParams!
) {{
  startPipelineExecution(
    executionParams: $executionParams,
  ) {{
    __typename
    ... on InvalidStepError {{
      invalidStepKey
    }}
    ... on InvalidOutputError {{
      stepKey
      invalidOutputName
    }}
    ... on PipelineConfigValidationInvalid {{
      pipeline {{
        name
      }}
      errors {{
        __typename
        message
        path
        reason
      }}
    }}
    ... on PipelineNotFoundError {{
        message
        pipelineName
    }}
    ... on StartPipelineExecutionSuccess {{
      run {{
        runId
        status
        pipeline {{
          name
        }}
        logs {{
          nodes {{
            __typename
            {step_event_fragment}
            {log_message_event_fragment}
          }}
          pageInfo {{
            lastCursor
            hasNextPage
            hasPreviousPage
            count
            totalCount
          }}
        }}
        environmentConfigYaml
        mode
      }}
    }}
  }}
}}
'''
