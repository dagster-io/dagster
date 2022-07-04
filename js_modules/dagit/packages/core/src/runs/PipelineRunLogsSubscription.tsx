import {gql} from '@apollo/client';

const PYTHON_ERROR_FRAGMENT = gql`
  fragment PythonErrorFragment on PythonError {
    __typename
    message
    stack
    cause {
      message
      stack
    }
  }
`;

const TABLE_SCHEMA_FRAGMENT = gql`
  fragment TableSchemaFragment on TableSchema {
    __typename
    columns {
      name
      description
      type
      constraints {
        nullable
        unique
        other
      }
    }
    constraints {
      other
    }
  }
`;

const METADATA_ENTRY_FRAGMENT = gql`
  fragment MetadataEntryFragment on MetadataEntry {
    __typename
    label
    description
    ... on PathMetadataEntry {
      path
    }
    ... on JsonMetadataEntry {
      jsonString
    }
    ... on UrlMetadataEntry {
      url
    }
    ... on TextMetadataEntry {
      text
    }
    ... on MarkdownMetadataEntry {
      mdStr
    }
    ... on PythonArtifactMetadataEntry {
      module
      name
    }
    ... on FloatMetadataEntry {
      floatValue
    }
    ... on IntMetadataEntry {
      intValue
      intRepr
    }
    ... on BoolMetadataEntry {
      boolValue
    }
    ... on PipelineRunMetadataEntry {
      runId
    }
    ... on AssetMetadataEntry {
      assetKey {
        path
      }
    }
    ... on TableMetadataEntry {
      table {
        records
        schema {
          ...TableSchemaFragment
        }
      }
    }
    ... on TableSchemaMetadataEntry {
      schema {
        ...TableSchemaFragment
      }
    }
  }
  ${TABLE_SCHEMA_FRAGMENT}
`;

const RUN_METADATA_PROVIDER_MESSAGE_FRAGMENT = gql`
  fragment RunMetadataProviderMessageFragment on DagsterRunEvent {
    __typename
    ... on MessageEvent {
      message
      timestamp
      stepKey
    }
    ... on MarkerEvent {
      markerStart
      markerEnd
    }
    ... on ObjectStoreOperationEvent {
      operationResult {
        op
        metadataEntries {
          ...MetadataEntryFragment
        }
      }
    }
    ... on LogsCapturedEvent {
      logKey
      stepKeys
      pid
    }
  }
  ${METADATA_ENTRY_FRAGMENT}
`;

const LOGS_ROW_STRUCTURED_FRAGMENT = gql`
  fragment LogsRowStructuredFragment on DagsterRunEvent {
    __typename
    ... on MessageEvent {
      message
      eventType
      timestamp
      level
      stepKey
    }
    ... on DisplayableEvent {
      label
      description
      metadataEntries {
        ...MetadataEntryFragment
      }
    }
    ... on MarkerEvent {
      markerStart
      markerEnd
    }
    ... on ErrorEvent {
      error {
        ...PythonErrorFragment
      }
    }
    ... on MaterializationEvent {
      assetKey {
        path
      }
    }
    ... on ObservationEvent {
      assetKey {
        path
      }
    }
    ... on ExecutionStepFailureEvent {
      errorSource
      failureMetadata {
        metadataEntries {
          ...MetadataEntryFragment
        }
      }
    }
    ... on ExecutionStepInputEvent {
      inputName
      typeCheck {
        label
        description
        success
        metadataEntries {
          ...MetadataEntryFragment
        }
      }
    }
    ... on ExecutionStepOutputEvent {
      outputName
      typeCheck {
        label
        description
        success
        metadataEntries {
          ...MetadataEntryFragment
        }
      }
    }
    ... on StepExpectationResultEvent {
      expectationResult {
        success
        label
        description
        metadataEntries {
          ...MetadataEntryFragment
        }
      }
    }
    ... on ObjectStoreOperationEvent {
      operationResult {
        op
        metadataEntries {
          ...MetadataEntryFragment
        }
      }
    }
    ... on HandledOutputEvent {
      outputName
      managerKey
    }
    ... on LoadedInputEvent {
      inputName
      managerKey
      upstreamOutputName
      upstreamStepKey
    }
    ... on LogsCapturedEvent {
      logKey
      stepKeys
    }
  }
  ${METADATA_ENTRY_FRAGMENT}
  ${PYTHON_ERROR_FRAGMENT}
`;

const LOGS_ROW_UNSTRUCTURED_FRAGMENT = gql`
  fragment LogsRowUnstructuredFragment on DagsterRunEvent {
    __typename
    ... on MessageEvent {
      message
      timestamp
      level
      stepKey
    }
  }
`;

const LOGS_SCROLLING_TABLE_MESSAGE_FRAGMENT = gql`
  fragment LogsScrollingTableMessageFragment on DagsterRunEvent {
    __typename
    ...LogsRowStructuredFragment
    ...LogsRowUnstructuredFragment
  }

  ${LOGS_ROW_STRUCTURED_FRAGMENT}
  ${LOGS_ROW_UNSTRUCTURED_FRAGMENT}
`;

const RUN_DAGSTER_RUN_EVENT_FRAGMENT = gql`
  fragment RunDagsterRunEventFragment on DagsterRunEvent {
    ... on MessageEvent {
      message
      timestamp
      level
      stepKey
    }

    ...LogsScrollingTableMessageFragment
    ...RunMetadataProviderMessageFragment
  }

  ${RUN_METADATA_PROVIDER_MESSAGE_FRAGMENT}
  ${LOGS_SCROLLING_TABLE_MESSAGE_FRAGMENT}
  ${PYTHON_ERROR_FRAGMENT}
`;

export const PIPELINE_RUN_LOGS_SUBSCRIPTION = gql`
  subscription PipelineRunLogsSubscription($runId: ID!, $cursor: String) {
    pipelineRunLogs(runId: $runId, cursor: $cursor) {
      __typename
      ... on PipelineRunLogsSubscriptionSuccess {
        messages {
          ... on MessageEvent {
            runId
          }
          ...RunDagsterRunEventFragment
        }
        hasMorePastEvents
        cursor
      }
      ... on PipelineRunLogsSubscriptionFailure {
        missingRunId
        message
      }
    }
  }

  ${RUN_DAGSTER_RUN_EVENT_FRAGMENT}
`;
