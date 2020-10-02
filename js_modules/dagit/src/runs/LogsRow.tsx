import {isEqual} from 'apollo-utilities';
import gql from 'graphql-tag';
import * as React from 'react';

import {showCustomAlert} from 'src/CustomAlertProvider';
import {PythonErrorInfo} from 'src/PythonErrorInfo';
import {IRunMetadataDict} from 'src/RunMetadataProvider';
import {setHighlightedGaantChartTime} from 'src/gaant/GaantChart';
import {CellTruncationProvider} from 'src/runs/CellTruncationProvider';
import {
  EventTypeColumn,
  Row,
  SolidColumn,
  StructuredContent,
  TimestampColumn,
} from 'src/runs/LogsRowComponents';
import {LogsRowStructuredContent} from 'src/runs/LogsRowStructuredContent';
import {MetadataEntry} from 'src/runs/MetadataEntry';
import {LogsRowStructuredFragment} from 'src/runs/types/LogsRowStructuredFragment';
import {LogsRowUnstructuredFragment} from 'src/runs/types/LogsRowUnstructuredFragment';
import {LogLevel} from 'src/types/globalTypes';

interface StructuredProps {
  node: LogsRowStructuredFragment;
  metadata: IRunMetadataDict;
  style: React.CSSProperties;
  textMatch: boolean;
}

interface StructuredState {
  expanded: boolean;
}

export class Structured extends React.Component<StructuredProps, StructuredState> {
  static fragments = {
    LogsRowStructuredFragment: gql`
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
      ${MetadataEntry.fragments.MetadataEntryFragment}
      ${PythonErrorInfo.fragments.PythonErrorFragment}
    `,
  };

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
          textMatch={this.props.textMatch}
        />
      </CellTruncationProvider>
    );
  }
}

const StructuredMemoizedContent: React.FunctionComponent<{
  node: LogsRowStructuredFragment;
  metadata: IRunMetadataDict;
  textMatch: boolean;
}> = React.memo(
  ({node, metadata, textMatch}) => (
    <Row
      level={LogLevel.INFO}
      onMouseEnter={() => setHighlightedGaantChartTime(node.timestamp)}
      onMouseLeave={() => setHighlightedGaantChartTime(null)}
      textMatch={textMatch}
    >
      <SolidColumn stepKey={'stepKey' in node && node.stepKey} />
      <StructuredContent>
        <LogsRowStructuredContent node={node} metadata={metadata} />
      </StructuredContent>
      <TimestampColumn time={'timestamp' in node && node.timestamp} />
    </Row>
  ),
  isEqual,
);

interface UnstructuredProps {
  node: LogsRowUnstructuredFragment;
  style: React.CSSProperties;
  textMatch: boolean;
}

export class Unstructured extends React.Component<UnstructuredProps> {
  static fragments = {
    LogsRowUnstructuredFragment: gql`
      fragment LogsRowUnstructuredFragment on PipelineRunEvent {
        __typename
        ... on MessageEvent {
          message
          timestamp
          level
          stepKey
        }
      }
    `,
  };

  onExpand = () => {
    showCustomAlert({
      body: <div style={{whiteSpace: 'pre-wrap'}}>{this.props.node.message}</div>,
    });
  };

  render() {
    return (
      <CellTruncationProvider style={this.props.style} onExpand={this.onExpand}>
        <UnstructuredMemoizedContent node={this.props.node} textMatch={this.props.textMatch} />
      </CellTruncationProvider>
    );
  }
}

const UnstructuredMemoizedContent: React.FunctionComponent<{
  node: LogsRowUnstructuredFragment;
  textMatch: boolean;
}> = React.memo(
  ({node, textMatch}) => (
    <Row
      level={node.level}
      onMouseEnter={() => setHighlightedGaantChartTime(node.timestamp)}
      onMouseLeave={() => setHighlightedGaantChartTime(null)}
      textMatch={textMatch}
    >
      <SolidColumn stepKey={node.stepKey} />
      <EventTypeColumn>{node.level}</EventTypeColumn>
      <span style={{flex: 1}}>{node.message}</span>
      <TimestampColumn time={node.timestamp} />
    </Row>
  ),
  isEqual,
);
