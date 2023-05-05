import {gql} from '@apollo/client';
import {Box} from '@dagster-io/ui';
import * as React from 'react';

import {showCustomAlert} from '../app/CustomAlertProvider';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {PythonErrorInfo} from '../app/PythonErrorInfo';
import {setHighlightedGanttChartTime} from '../gantt/GanttChart';
import {LogLevel} from '../graphql/types';
import {METADATA_ENTRY_FRAGMENT} from '../metadata/MetadataEntry';

import {CellTruncationProvider} from './CellTruncationProvider';
import {
  EventTypeColumn,
  Row,
  OpColumn,
  StructuredContent,
  TimestampColumn,
} from './LogsRowComponents';
import {LogsRowStructuredContent} from './LogsRowStructuredContent';
import {IRunMetadataDict} from './RunMetadataProvider';
import {LogsRowStructuredFragment, LogsRowUnstructuredFragment} from './types/LogsRow.types';

interface StructuredProps {
  node: LogsRowStructuredFragment;
  metadata: IRunMetadataDict;
  style: React.CSSProperties;
  highlighted: boolean;
}

interface StructuredState {
  expanded: boolean;
}

export class Structured extends React.Component<StructuredProps, StructuredState> {
  onExpand = () => {
    const {node, metadata} = this.props;

    if (node.__typename === 'ExecutionStepFailureEvent') {
      showCustomAlert({
        title: 'Error',
        body: (
          <PythonErrorInfo
            error={node.error ? node.error : node}
            failureMetadata={node.failureMetadata}
            errorSource={node.errorSource}
          />
        ),
      });
    } else if (node.__typename === 'ExecutionStepUpForRetryEvent') {
      showCustomAlert({
        title: 'Step Retry',
        body: <PythonErrorInfo error={node.error ? node.error : node} />,
      });
    } else if (
      (node.__typename === 'EngineEvent' && node.error) ||
      (node.__typename === 'RunFailureEvent' && node.error) ||
      node.__typename === 'HookErroredEvent' ||
      node.__typename === 'ResourceInitFailureEvent'
    ) {
      showCustomAlert({
        title: 'Error',
        body: <PythonErrorInfo error={node.error ? node.error : node} />,
      });
    } else {
      showCustomAlert({
        title: node.stepKey || 'Info',
        body: (
          <StructuredContent>
            <LogsRowStructuredContent node={node} metadata={metadata} />
          </StructuredContent>
        ),
      });
    }
  };

  render() {
    return (
      <CellTruncationProvider style={this.props.style} onExpand={this.onExpand}>
        <StructuredMemoizedContent
          node={this.props.node}
          metadata={this.props.metadata}
          highlighted={this.props.highlighted}
        />
      </CellTruncationProvider>
    );
  }
}

export const LOGS_ROW_STRUCTURED_FRAGMENT = gql`
  fragment LogsRowStructuredFragment on DagsterRunEvent {
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
      fileKey
      stepKeys
      externalUrl
      externalStdoutUrl
      externalStderrUrl
    }
  }

  ${METADATA_ENTRY_FRAGMENT}
  ${PYTHON_ERROR_FRAGMENT}
`;

const StructuredMemoizedContent: React.FC<{
  node: LogsRowStructuredFragment;
  metadata: IRunMetadataDict;
  highlighted: boolean;
}> = React.memo(({node, metadata, highlighted}) => {
  const stepKey = node.stepKey;
  const step = stepKey ? metadata.steps[stepKey] : null;
  const stepStartTime = step?.start;

  return (
    <Row
      level={LogLevel.INFO}
      onMouseEnter={() => setHighlightedGanttChartTime(node.timestamp)}
      onMouseLeave={() => setHighlightedGanttChartTime(null)}
      highlighted={highlighted}
    >
      <TimestampColumn
        time={'timestamp' in node ? node.timestamp : null}
        runStartTime={metadata.startedPipelineAt}
        stepStartTime={stepStartTime}
      />
      <OpColumn stepKey={'stepKey' in node && node.stepKey} />
      <StructuredContent>
        <LogsRowStructuredContent node={node} metadata={metadata} />
      </StructuredContent>
    </Row>
  );
});

StructuredMemoizedContent.displayName = 'StructuredMemoizedContent';

interface UnstructuredProps {
  node: LogsRowUnstructuredFragment;
  style: React.CSSProperties;
  highlighted: boolean;
  metadata: IRunMetadataDict;
}

export class Unstructured extends React.Component<UnstructuredProps> {
  onExpand = () => {
    showCustomAlert({
      title: 'Log',
      body: <div style={{whiteSpace: 'pre-wrap'}}>{this.props.node.message}</div>,
    });
  };

  render() {
    return (
      <CellTruncationProvider style={this.props.style} onExpand={this.onExpand}>
        <UnstructuredMemoizedContent
          node={this.props.node}
          highlighted={this.props.highlighted}
          metadata={this.props.metadata}
        />
      </CellTruncationProvider>
    );
  }
}

export const LOGS_ROW_UNSTRUCTURED_FRAGMENT = gql`
  fragment LogsRowUnstructuredFragment on DagsterRunEvent {
    ... on MessageEvent {
      message
      timestamp
      level
      stepKey
    }
  }
`;

const UnstructuredMemoizedContent: React.FC<{
  node: LogsRowUnstructuredFragment;
  metadata: IRunMetadataDict;
  highlighted: boolean;
}> = React.memo(({node, highlighted, metadata}) => {
  const stepKey = node.stepKey;
  const step = stepKey ? metadata.steps[stepKey] : null;
  const stepStartTime = step?.start;

  return (
    <Row
      level={node.level}
      onMouseEnter={() => setHighlightedGanttChartTime(node.timestamp)}
      onMouseLeave={() => setHighlightedGanttChartTime(null)}
      highlighted={highlighted}
    >
      <TimestampColumn
        time={node.timestamp}
        runStartTime={metadata.startedPipelineAt}
        stepStartTime={stepStartTime}
      />
      <OpColumn stepKey={node.stepKey} />
      <EventTypeColumn>
        <span style={{marginLeft: 8}}>{node.level}</span>
      </EventTypeColumn>
      <Box padding={{horizontal: 12}} style={{flex: 1}}>
        {node.message}
      </Box>
    </Row>
  );
});

UnstructuredMemoizedContent.displayName = 'UnstructuredMemoizedContent';
