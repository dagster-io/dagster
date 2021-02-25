import {Colors, Intent, Tag} from '@blueprintjs/core';
import * as React from 'react';

import {assertUnreachable} from 'src/app/Util';
import {PythonErrorFragment} from 'src/app/types/PythonErrorFragment';
import {ComputeLogLink} from 'src/runs/ComputeLogModal';
import {EventTypeColumn} from 'src/runs/LogsRowComponents';
import {
  LogRowStructuredContentTable,
  MetadataEntries,
  MetadataEntryAction,
  MetadataEntryLink,
} from 'src/runs/MetadataEntry';
import {IRunMetadataDict} from 'src/runs/RunMetadataProvider';
import {
  LogsRowStructuredFragment,
  LogsRowStructuredFragment_StepMaterializationEvent_materialization,
} from 'src/runs/types/LogsRowStructuredFragment';
import {MetadataEntryFragment} from 'src/runs/types/MetadataEntryFragment';
import {ErrorSource} from 'src/types/globalTypes';

interface IStructuredContentProps {
  node: LogsRowStructuredFragment;
  metadata: IRunMetadataDict;
}

export const LogsRowStructuredContent: React.FC<IStructuredContentProps> = ({node, metadata}) => {
  const eventType = node.eventType as string;
  switch (node.__typename) {
    // Errors
    case 'PipelineInitFailureEvent':
      return <FailureContent error={node.error} eventType={eventType} />;
    case 'ExecutionStepFailureEvent':
      return (
        <FailureContent
          eventType={eventType}
          error={node.error}
          metadataEntries={node?.failureMetadata?.metadataEntries}
          errorSource={node.errorSource}
        />
      );

    case 'ExecutionStepUpForRetryEvent':
      return <DefaultContent eventType={eventType} message={node.message} eventIntent="warning" />;

    case 'ExecutionStepStartEvent':
      if (!node.stepKey) {
        return <DefaultContent message={node.message} eventType={eventType} />;
      } else {
        return (
          <DefaultContent message={node.message} eventType={eventType}>
            <LogRowStructuredContentTable
              rows={[
                {
                  label: 'step_logs',
                  item: (
                    <ComputeLogLink
                      stepKey={node.stepKey}
                      runState={metadata.steps[node.stepKey]?.state}
                    >
                      <MetadataEntryAction>View Raw Step Output</MetadataEntryAction>
                    </ComputeLogLink>
                  ),
                },
              ]}
            />
          </DefaultContent>
        );
      }
    case 'ExecutionStepSkippedEvent':
      return (
        <DefaultContent
          message={node.message}
          eventType={eventType}
          eventColor="rgba(173, 185, 152, 0.3)"
        />
      );

    case 'ExecutionStepRestartEvent':
      return <DefaultContent message={node.message} eventType={eventType} />;

    case 'ExecutionStepSuccessEvent':
      return <DefaultContent message={node.message} eventType={eventType} eventIntent="success" />;
    case 'ExecutionStepInputEvent':
      return (
        <DefaultContent
          message={
            node.message + (node.typeCheck.description ? ' ' + node.typeCheck.description : '')
          }
          eventType={eventType}
          eventIntent={node.typeCheck.success ? 'success' : 'warning'}
        >
          <MetadataEntries entries={node.typeCheck.metadataEntries} />
        </DefaultContent>
      );
    case 'ExecutionStepOutputEvent':
      return (
        <DefaultContent
          message={
            node.message + (node.typeCheck.description ? ' ' + node.typeCheck.description : '')
          }
          eventType={eventType}
          eventIntent={node.typeCheck.success ? 'success' : 'warning'}
        >
          <MetadataEntries entries={node.typeCheck.metadataEntries} />
        </DefaultContent>
      );
    case 'StepExpectationResultEvent':
      return (
        <DefaultContent
          message={node.message}
          eventType={eventType}
          eventIntent={node.expectationResult.success ? 'success' : 'warning'}
        >
          <MetadataEntries entries={node.expectationResult.metadataEntries} />
        </DefaultContent>
      );
    case 'StepMaterializationEvent':
      return (
        <MaterializationContent
          message={node.message}
          materialization={node.materialization}
          eventType={eventType}
        />
      );
    case 'ObjectStoreOperationEvent':
      return (
        <DefaultContent message={node.message} eventType={eventType}>
          <MetadataEntries entries={node.operationResult.metadataEntries} />
        </DefaultContent>
      );
    case 'HandledOutputEvent':
      return <DefaultContent message={node.message} eventType={eventType} />;
    case 'LoadedInputEvent':
      return <DefaultContent message={node.message} eventType={eventType} />;
    case 'HookCompletedEvent':
      return <DefaultContent eventType={eventType} message={node.message} />;
    case 'HookSkippedEvent':
      return <DefaultContent eventType={eventType} message={node.message} />;
    case 'HookErroredEvent':
      return <FailureContent eventType={eventType} error={node.error} />;
    case 'PipelineFailureEvent':
      if (node.pipelineFailureError) {
        return (
          <FailureContent
            message={node.message}
            error={node.pipelineFailureError}
            eventType={eventType}
          />
        );
      }

      return <DefaultContent message={node.message} eventType={eventType} eventIntent="danger" />;
    case 'PipelineSuccessEvent':
      return <DefaultContent message={node.message} eventType={eventType} eventIntent="success" />;

    case 'PipelineStartEvent':
      return <DefaultContent message={node.message} eventType={eventType} />;
    case 'PipelineEnqueuedEvent':
      return <DefaultContent message={node.message} eventType={eventType} />;
    case 'PipelineDequeuedEvent':
      return <DefaultContent message={node.message} eventType={eventType} />;
    case 'PipelineStartingEvent':
      return <DefaultContent message={node.message} eventType={eventType} />;
    case 'PipelineCancelingEvent':
      return <DefaultContent message={node.message} eventType={eventType} />;
    case 'PipelineCanceledEvent':
      return <FailureContent message={node.message} eventType={eventType} />;
    case 'EngineEvent':
      if (node.engineError) {
        return (
          <FailureContent message={node.message} error={node.engineError} eventType={eventType} />
        );
      }
      return (
        <DefaultContent
          message={node.message}
          eventType={eventType}
          eventColor="rgba(27,164,206,0.2)"
        >
          <MetadataEntries entries={node.metadataEntries} />
        </DefaultContent>
      );
    case 'LogMessageEvent':
      return <DefaultContent message={node.message} />;
    default:
      // This allows us to check that the switch is exhaustive because the union type should
      // have been narrowed following each successive case to `never` at this point.
      return assertUnreachable(node);
  }
};

// Structured Content Renderers

const DefaultContent: React.FunctionComponent<{
  message: string;
  eventType?: string;
  eventColor?: string;
  eventIntent?: Intent;
  metadataEntries?: MetadataEntryFragment[];
  children?: React.ReactElement;
}> = ({message, eventType, eventColor, eventIntent, children}) => {
  return (
    <>
      <EventTypeColumn>
        {eventType && (
          <Tag
            minimal={true}
            intent={eventIntent}
            style={
              eventColor
                ? {
                    fontSize: '0.9em',
                    color: 'black',
                    background: eventColor,
                  }
                : {
                    fontSize: '0.9em',
                  }
            }
          >
            {eventType}
          </Tag>
        )}
      </EventTypeColumn>
      <span style={{flex: 1}}>
        {message}
        {children}
      </span>
    </>
  );
};

const FailureContent: React.FunctionComponent<{
  message?: string;
  eventType: string;
  error?: PythonErrorFragment;
  errorSource?: ErrorSource | null;
  metadataEntries?: MetadataEntryFragment[];
}> = ({message, error, errorSource, eventType, metadataEntries}) => {
  let contextMessage = null;
  let errorMessage = null;
  let errorStack = null;
  let errorCause = null;

  if (message) {
    contextMessage = (
      <>
        <span>{message}</span>
        <br />
      </>
    );
  }

  if (error) {
    errorMessage = <span style={{color: Colors.RED3}}>{`${error.message}`}</span>;

    // omit the outer stack for user code errors with a cause
    // as the outer stack is just framework code
    if (!(errorSource == ErrorSource.USER_CODE_ERROR && error.cause)) {
      errorStack = <span style={{color: Colors.RED3}}>{`\nStack Trace:\n${error.stack}`}</span>;
    }

    if (error.cause) {
      errorCause = (
        <>
          {`The above exception was caused by the following exception:\n`}
          <span style={{color: Colors.RED3}}>{`${error.cause.message}`}</span>
          <span style={{color: Colors.RED3}}>{`\nStack Trace:\n${error.cause.stack}`}</span>
        </>
      );
    }
  }

  return (
    <>
      <EventTypeColumn>
        <Tag minimal={true} intent="danger" style={{fontSize: '0.9em'}}>
          {eventType}
        </Tag>
      </EventTypeColumn>
      <span style={{flex: 1}}>
        {contextMessage}
        {errorMessage}
        <MetadataEntries entries={metadataEntries} />
        {errorStack}
        {errorCause}
      </span>
    </>
  );
};
const MaterializationContent: React.FC<{
  message: string;
  materialization: LogsRowStructuredFragment_StepMaterializationEvent_materialization;
  eventType: string;
}> = ({message, materialization, eventType}) => {
  if (!materialization.assetKey) {
    return (
      <DefaultContent message={message} eventType={eventType}>
        <MetadataEntries entries={materialization.metadataEntries} />
      </DefaultContent>
    );
  }

  const assetDashboardLink = (
    <span style={{marginLeft: 10}}>
      [
      <MetadataEntryLink
        to={`/instance/assets/${materialization.assetKey.path.map(encodeURIComponent).join('/')}`}
      >
        View Asset
      </MetadataEntryLink>
      ]
    </span>
  );

  return (
    <DefaultContent message={message} eventType={eventType}>
      <>
        <LogRowStructuredContentTable
          rows={[
            {
              label: 'asset_key',
              item: (
                <>
                  {materialization.assetKey.path.join(' > ')}
                  {assetDashboardLink}
                </>
              ),
            },
          ]}
          styles={{paddingBottom: 0}}
        />
        <MetadataEntries entries={materialization.metadataEntries} />
      </>
    </DefaultContent>
  );
};
