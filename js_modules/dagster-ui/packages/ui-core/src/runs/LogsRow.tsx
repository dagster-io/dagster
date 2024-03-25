import {gql} from '@apollo/client';
import {Box, Button, Dialog, DialogBody, DialogFooter} from '@dagster-io/ui-components';
import * as React from 'react';
import {useMemo, useState} from 'react';

import {CellTruncationProvider} from './CellTruncationProvider';
import {
  EventTypeColumn,
  OpColumn,
  Row,
  StructuredContent,
  TimestampColumn,
} from './LogsRowComponents';
import {LogsRowStructuredContent} from './LogsRowStructuredContent';
import {IRunMetadataDict} from './RunMetadataProvider';
import {LogsRowStructuredFragment, LogsRowUnstructuredFragment} from './types/LogsRow.types';
import {showCustomAlert} from '../app/CustomAlertProvider';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {PythonErrorInfo} from '../app/PythonErrorInfo';
import {setHighlightedGanttChartTime} from '../gantt/GanttChart';
import {LogLevel} from '../graphql/types';
import {METADATA_ENTRY_FRAGMENT} from '../metadata/MetadataEntry';
import {autolinkTextContent} from '../ui/autolinking';

interface StructuredProps {
  node: LogsRowStructuredFragment;
  metadata: IRunMetadataDict;
  style: React.CSSProperties;
  highlighted: boolean;
}

export const Structured = (props: StructuredProps) => {
  const {node, metadata, style, highlighted} = props;
  const [expanded, setExpanded] = useState(false);

  const {title, body} = useMemo(() => {
    if (node.__typename === 'ExecutionStepFailureEvent') {
      return {
        title: 'Error',
        body: (
          <PythonErrorInfo
            error={node.error ? node.error : node}
            failureMetadata={node.failureMetadata}
            errorSource={node.errorSource}
          />
        ),
      };
    }

    if (node.__typename === 'ExecutionStepUpForRetryEvent') {
      return {
        title: 'Step Retry',
        body: <PythonErrorInfo error={node.error ? node.error : node} />,
      };
    }

    if (
      (node.__typename === 'EngineEvent' && node.error) ||
      (node.__typename === 'RunFailureEvent' && node.error) ||
      node.__typename === 'HookErroredEvent' ||
      node.__typename === 'ResourceInitFailureEvent'
    ) {
      return {
        title: 'Error',
        body: <PythonErrorInfo error={node.error ? node.error : node} />,
      };
    }

    return {
      title: node.stepKey || 'Info',
      body: (
        <StructuredContent>
          <LogsRowStructuredContent node={node} metadata={metadata} />
        </StructuredContent>
      ),
    };
  }, [metadata, node]);

  return (
    <CellTruncationProvider style={style} onExpand={() => setExpanded(true)}>
      <StructuredMemoizedContent node={node} metadata={metadata} highlighted={highlighted} />
      <Dialog
        title={title}
        isOpen={expanded}
        canEscapeKeyClose
        canOutsideClickClose
        onClose={() => setExpanded(false)}
        style={{width: 'auto', maxWidth: '80vw'}}
      >
        <DialogBody>{body}</DialogBody>
        <DialogFooter topBorder>
          <Button intent="primary" onClick={() => setExpanded(false)}>
            Done
          </Button>
        </DialogFooter>
      </Dialog>
    </CellTruncationProvider>
  );
};

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
    ... on AssetCheckEvaluationEvent {
      evaluation {
        checkName
        success
        timestamp
        assetKey {
          path
        }
        targetMaterialization {
          timestamp
        }
        metadataEntries {
          ...MetadataEntryFragment
        }
      }
    }
  }

  ${METADATA_ENTRY_FRAGMENT}
  ${PYTHON_ERROR_FRAGMENT}
`;

interface StructuredMemoizedContentProps {
  node: LogsRowStructuredFragment;
  metadata: IRunMetadataDict;
  highlighted: boolean;
}

const StructuredMemoizedContent = React.memo((props: StructuredMemoizedContentProps) => {
  const {node, metadata, highlighted} = props;
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

export const UnstructuredDialogContent = ({message}: {message: string}) => {
  const messageEl = React.createRef<HTMLDivElement>();
  React.useEffect(() => {
    if (messageEl.current) {
      autolinkTextContent(messageEl.current, {useIdleCallback: true});
    }
  }, [message, messageEl]);

  return (
    <div style={{whiteSpace: 'pre-wrap', maxHeight: '70vh', overflow: 'auto'}} ref={messageEl}>
      {message}
    </div>
  );
};

export class Unstructured extends React.Component<UnstructuredProps> {
  onExpand = () => {
    showCustomAlert({
      title: 'Log',
      body: <UnstructuredDialogContent message={this.props.node.message} />,
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

interface UnstructuredMemoizedContentProps {
  node: LogsRowUnstructuredFragment;
  metadata: IRunMetadataDict;
  highlighted: boolean;
}

const UnstructuredMemoizedContent = React.memo((props: UnstructuredMemoizedContentProps) => {
  const {node, highlighted, metadata} = props;
  const stepKey = node.stepKey;
  const step = stepKey ? metadata.steps[stepKey] : null;
  const stepStartTime = step?.start;

  // Note: We need to render enough of our text content that the TruncationProvider wrapping the
  // element knows whether to show "View full message", but that shows a modal with the full
  // message - the full text is never needed in the log table. Clip to a max of 15,000 characters
  // to avoid rendering 1M characters in a small box. 15k is 2700x580px with no whitespace.
  const messageClipped = node.message.length > 15000 ? node.message.slice(0, 15000) : node.message;
  const messageEl = React.createRef<HTMLDivElement>();
  React.useEffect(() => {
    if (messageEl.current) {
      autolinkTextContent(messageEl.current, {useIdleCallback: messageClipped.length > 5000});
    }
  }, [messageClipped, messageEl]);

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
      <Box padding={{horizontal: 12}} style={{flex: 1}} ref={messageEl}>
        {messageClipped}
      </Box>
    </Row>
  );
});

UnstructuredMemoizedContent.displayName = 'UnstructuredMemoizedContent';
