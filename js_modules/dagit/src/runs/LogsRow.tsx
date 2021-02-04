import {gql} from '@apollo/client';
import * as React from 'react';

import {showCustomAlert} from 'src/app/CustomAlertProvider';
import {PythonErrorInfo, PYTHON_ERROR_FRAGMENT} from 'src/app/PythonErrorInfo';
import {setHighlightedGanttChartTime} from 'src/gantt/GanttChart';
import {CellTruncationProvider} from 'src/runs/CellTruncationProvider';
import {
  EventTypeColumn,
  Row,
  SolidColumn,
  StructuredContent,
  TimestampColumn,
} from 'src/runs/LogsRowComponents';
import {LogsRowStructuredContent} from 'src/runs/LogsRowStructuredContent';
import {METADATA_ENTRY_FRAGMENT} from 'src/runs/MetadataEntry';
import {IRunMetadataDict} from 'src/runs/RunMetadataProvider';
import {LogsRowStructuredFragment} from 'src/runs/types/LogsRowStructuredFragment';
import {LogsRowUnstructuredFragment} from 'src/runs/types/LogsRowUnstructuredFragment';
import {LogLevel} from 'src/types/globalTypes';

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
        body: <PythonErrorInfo error={node.error} failureMetadata={node.failureMetadata} />,
      });
    } else if (node.__typename === 'HookErroredEvent') {
      showCustomAlert({
        title: 'Error',
        body: <PythonErrorInfo error={node.error} />,
      });
    } else if (node.__typename === 'PipelineInitFailureEvent') {
      showCustomAlert({
        title: 'Error',
        body: <PythonErrorInfo error={node.error} />,
      });
    } else if (node.__typename === 'EngineEvent' && node.engineError) {
      showCustomAlert({
        title: 'Error',
        body: <PythonErrorInfo error={node.engineError} />,
      });
    } else if (node.__typename === 'PipelineFailureEvent' && node.pipelineFailureError) {
      showCustomAlert({
        title: 'Error',
        body: <PythonErrorInfo error={node.pipelineFailureError} />,
      });
    } else {
      showCustomAlert({
        title: (node.stepKey && node.stepKey) || 'Info',
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
  fragment LogsRowStructuredFragment on PipelineRunEvent {
    __typename
    ... on MessageEvent {
      message
      timestamp
      level
      stepKey
    }
    ... on StepMaterializationEvent {
      materialization {
        assetKey {
          path
        }
        label
        description
        metadataEntries {
          ...MetadataEntryFragment
        }
      }
    }
    ... on PipelineInitFailureEvent {
      error {
        ...PythonErrorFragment
      }
    }
    ... on PipelineFailureEvent {
      pipelineFailureError: error {
        ...PythonErrorFragment
      }
    }
    ... on ExecutionStepFailureEvent {
      error {
        ...PythonErrorFragment
      }
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
    ... on EngineEvent {
      metadataEntries {
        ...MetadataEntryFragment
      }
      engineError: error {
        ...PythonErrorFragment
      }
    }
    ... on HookErroredEvent {
      error {
        ...PythonErrorFragment
      }
    }
  }
  ${METADATA_ENTRY_FRAGMENT}
  ${PYTHON_ERROR_FRAGMENT}
`;

const StructuredMemoizedContent: React.FunctionComponent<{
  node: LogsRowStructuredFragment;
  metadata: IRunMetadataDict;
  highlighted: boolean;
}> = React.memo(({node, metadata, highlighted}) => (
  <Row
    level={LogLevel.INFO}
    onMouseEnter={() => setHighlightedGanttChartTime(node.timestamp)}
    onMouseLeave={() => setHighlightedGanttChartTime(null)}
    highlighted={highlighted}
  >
    <SolidColumn stepKey={'stepKey' in node && node.stepKey} />
    <StructuredContent>
      <LogsRowStructuredContent node={node} metadata={metadata} />
    </StructuredContent>
    <TimestampColumn time={'timestamp' in node && node.timestamp} />
  </Row>
));

interface UnstructuredProps {
  node: LogsRowUnstructuredFragment;
  style: React.CSSProperties;
  highlighted: boolean;
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
        <UnstructuredMemoizedContent node={this.props.node} highlighted={this.props.highlighted} />
      </CellTruncationProvider>
    );
  }
}

export const LOGS_ROW_UNSTRUCTURED_FRAGMENT = gql`
  fragment LogsRowUnstructuredFragment on PipelineRunEvent {
    __typename
    ... on MessageEvent {
      message
      timestamp
      level
      stepKey
    }
  }
`;

const UnstructuredMemoizedContent: React.FunctionComponent<{
  node: LogsRowUnstructuredFragment;
  highlighted: boolean;
}> = React.memo(({node, highlighted}) => (
  <Row
    level={node.level}
    onMouseEnter={() => setHighlightedGanttChartTime(node.timestamp)}
    onMouseLeave={() => setHighlightedGanttChartTime(null)}
    highlighted={highlighted}
  >
    <SolidColumn stepKey={node.stepKey} />
    <EventTypeColumn>{node.level}</EventTypeColumn>
    <span style={{flex: 1}}>{node.message}</span>
    <TimestampColumn time={node.timestamp} />
  </Row>
));
