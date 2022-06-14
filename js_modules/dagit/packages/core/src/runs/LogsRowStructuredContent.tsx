// eslint-disable-next-line no-restricted-imports
import {Intent} from '@blueprintjs/core';
import {Box, Colors, Tag} from '@dagster-io/ui';
import qs from 'qs';
import * as React from 'react';
import {Link, useLocation} from 'react-router-dom';

import {assertUnreachable} from '../app/Util';
import {PythonErrorFragment} from '../app/types/PythonErrorFragment';
import {displayNameForAssetKey} from '../asset-graph/Utils';
import {assetDetailsPathForKey} from '../assets/assetDetailsPathForKey';
import {AssetKey} from '../assets/types';
import {
  LogRowStructuredContentTable,
  MetadataEntries,
  MetadataEntryLink,
} from '../metadata/MetadataEntry';
import {MetadataEntryFragment} from '../metadata/types/MetadataEntryFragment';
import {DagsterEventType, ErrorSource} from '../types/globalTypes';

import {EventTypeColumn} from './LogsRowComponents';
import {IRunMetadataDict} from './RunMetadataProvider';
import {eventTypeToDisplayType} from './getRunFilterProviders';
import {LogsRowStructuredFragment} from './types/LogsRowStructuredFragment';

interface IStructuredContentProps {
  node: LogsRowStructuredFragment;
  metadata: IRunMetadataDict;
}

export const LogsRowStructuredContent: React.FC<IStructuredContentProps> = ({node, metadata}) => {
  const location = useLocation();
  const eventType = node.eventType as string;
  switch (node.__typename) {
    case 'ExecutionStepFailureEvent':
      return (
        <FailureContent
          eventType={eventType}
          error={node.error}
          metadataEntries={node?.failureMetadata?.metadataEntries}
          errorSource={node.errorSource}
          message={node.error ? undefined : node.message}
        />
      );

    case 'ExecutionStepUpForRetryEvent':
      return <StepUpForRetryContent error={node.error} message={node.message} />;

    case 'ExecutionStepStartEvent':
      if (!node.stepKey || metadata.logCaptureSteps) {
        return <DefaultContent message={node.message} eventType={eventType} />;
      } else {
        const currentQuery = qs.parse(location.search);
        const updatedQuery = {
          ...currentQuery,
          logType: 'stdout',
          logs: `query:${node.stepKey}`,
          selection: node.stepKey,
        };
        const href = `${location.pathname}?${qs.stringify(updatedQuery)}`;
        return (
          <DefaultContent message={node.message} eventType={eventType}>
            <LogRowStructuredContentTable
              rows={[
                {
                  label: 'step_logs',
                  item: (
                    <Link to={href} style={{color: 'inherit'}}>
                      View Raw Step Output
                    </Link>
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
          <>
            <MetadataEntries entries={node.typeCheck.metadataEntries} />
            <MetadataEntries entries={node.metadataEntries} />
          </>
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
    case 'MaterializationEvent':
      return (
        <AssetMetadataContent
          message={node.message}
          assetKey={node.assetKey}
          metadataEntries={node.metadataEntries}
          eventType={eventType}
          timestamp={node.timestamp}
        />
      );
    case 'ObservationEvent':
      return (
        <AssetMetadataContent
          message=""
          assetKey={node.assetKey}
          metadataEntries={node.metadataEntries}
          eventType={eventType}
          timestamp={node.timestamp}
        />
      );
    case 'AssetMaterializationPlannedEvent':
      return <DefaultContent eventType={eventType} message={node.message} />;
    case 'ObjectStoreOperationEvent':
      return (
        <DefaultContent message={node.message} eventType={eventType}>
          <MetadataEntries entries={node.operationResult.metadataEntries} />
        </DefaultContent>
      );
    case 'HandledOutputEvent':
      return (
        <DefaultContent message={node.message} eventType={eventType}>
          <MetadataEntries entries={node.metadataEntries} />
        </DefaultContent>
      );
    case 'LoadedInputEvent':
      return (
        <DefaultContent message={node.message} eventType={eventType}>
          <MetadataEntries entries={node.metadataEntries} />
        </DefaultContent>
      );
    case 'HookCompletedEvent':
      return <DefaultContent eventType={eventType} message={node.message} />;
    case 'HookSkippedEvent':
      return <DefaultContent eventType={eventType} message={node.message} />;
    case 'HookErroredEvent':
      return <FailureContent eventType={eventType} error={node.error} />;
    case 'AlertStartEvent':
      return <DefaultContent eventType={eventType} message={node.message} />;
    case 'AlertSuccessEvent':
      return <DefaultContent eventType={eventType} message={node.message} eventIntent="success" />;
    case 'AlertFailureEvent':
      return <DefaultContent eventType={eventType} message={node.message} eventIntent="warning" />;
    case 'RunFailureEvent':
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
    case 'RunSuccessEvent':
      return <DefaultContent message={node.message} eventType={eventType} eventIntent="success" />;

    case 'RunStartEvent':
      return <DefaultContent message={node.message} eventType={eventType} />;
    case 'RunEnqueuedEvent':
      return <DefaultContent message={node.message} eventType={eventType} />;
    case 'RunDequeuedEvent':
      return <DefaultContent message={node.message} eventType={eventType} />;
    case 'RunStartingEvent':
      return <DefaultContent message={node.message} eventType={eventType} />;
    case 'RunCancelingEvent':
      return <DefaultContent message={node.message} eventType={eventType} />;
    case 'RunCanceledEvent':
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
    case 'LogsCapturedEvent':
      const currentQuery = qs.parse(location.search, {ignoreQueryPrefix: true});
      const updatedQuery = {...currentQuery, logType: 'stdout', logKey: node.stepKey};
      const rawLogsUrl = `${location.pathname}?${qs.stringify(updatedQuery)}`;
      const rawLogsLink = (
        <Link to={rawLogsUrl} style={{color: 'inherit'}}>
          View stdout / stderr
        </Link>
      );
      const rows = node.stepKey
        ? [
            {
              label: 'captured_logs',
              item: rawLogsLink,
            },
          ]
        : [
            {
              label: 'step_keys',
              item: <>{JSON.stringify(node.stepKeys)}</>,
            },
            {
              label: 'captured_logs',
              item: rawLogsLink,
            },
          ];
      return (
        <DefaultContent eventType={eventType} message={node.message}>
          <LogRowStructuredContentTable rows={rows} />
        </DefaultContent>
      );
    default:
      // This allows us to check that the switch is exhaustive because the union type should
      // have been narrowed following each successive case to `never` at this point.
      return assertUnreachable(node);
  }
};

// Structured Content Renderers

const DefaultContent: React.FC<{
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
            {eventTypeToDisplayType(eventType)}
          </Tag>
        )}
      </EventTypeColumn>
      <Box padding={{horizontal: 12}} style={{flex: 1}}>
        {message}
        {children}
      </Box>
    </>
  );
};

const FailureContent: React.FC<{
  message?: string;
  eventType: string;
  error?: PythonErrorFragment | null;
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
    errorMessage = <span style={{color: Colors.Red500}}>{`${error.message}`}</span>;

    // omit the outer stack for user code errors with a cause
    // as the outer stack is just framework code
    if (!(errorSource === ErrorSource.USER_CODE_ERROR && error.cause)) {
      errorStack = <span style={{color: Colors.Red500}}>{`\nStack Trace:\n${error.stack}`}</span>;
    }

    if (error.cause) {
      errorCause = (
        <>
          {`The above exception was caused by the following exception:\n`}
          <span style={{color: Colors.Red500}}>{`${error.cause.message}`}</span>
          <span style={{color: Colors.Red500}}>{`\nStack Trace:\n${error.cause.stack}`}</span>
        </>
      );
    }
  }

  return (
    <>
      <EventTypeColumn>
        <Tag minimal intent="danger">
          {eventTypeToDisplayType(eventType)}
        </Tag>
      </EventTypeColumn>
      <Box padding={{horizontal: 12}} style={{flex: 1}}>
        {contextMessage}
        {errorMessage}
        <MetadataEntries entries={metadataEntries} />
        {errorStack}
        {errorCause}
      </Box>
    </>
  );
};

const StepUpForRetryContent: React.FC<{
  message?: string;
  error?: PythonErrorFragment | null;
}> = ({message, error}) => {
  let contextMessage = null;
  let errorCause = null;
  let errorMessage = null;
  let errorStack = null;

  if (message) {
    contextMessage = (
      <>
        <span>{message}</span>
        <br />
      </>
    );
  }

  if (error) {
    // If no cause, this was a `raise RetryRequest` inside the op. Show the trace for the main error.
    if (!error.cause) {
      errorMessage = <span style={{color: Colors.Red500}}>{`${error.message}`}</span>;
      errorStack = <span style={{color: Colors.Red500}}>{`\nStack Trace:\n${error.stack}`}</span>;
    } else {
      // If there is a cause, this was a different exception. Show that instead.
      errorCause = (
        <>
          {`The retry request was caused by the following exception:\n`}
          <span style={{color: Colors.Red500}}>{`${error.cause.message}`}</span>
          <span style={{color: Colors.Red500}}>{`\nStack Trace:\n${error.cause.stack}`}</span>
        </>
      );
    }
  }

  return (
    <>
      <EventTypeColumn>
        <Tag minimal intent="warning">
          {eventTypeToDisplayType(DagsterEventType.STEP_UP_FOR_RETRY)}
        </Tag>
      </EventTypeColumn>
      <Box padding={{horizontal: 12}} style={{flex: 1}}>
        {contextMessage}
        {errorMessage}
        {errorStack}
        {errorCause}
      </Box>
    </>
  );
};

const AssetMetadataContent: React.FC<{
  message: string;
  assetKey: AssetKey | null;
  metadataEntries: MetadataEntryFragment[];
  eventType: string;
  timestamp: string;
}> = ({message, assetKey, metadataEntries, eventType, timestamp}) => {
  if (!assetKey) {
    return (
      <DefaultContent message={message} eventType={eventType}>
        <MetadataEntries entries={metadataEntries} />
      </DefaultContent>
    );
  }

  const to = assetDetailsPathForKey(assetKey, {asOf: timestamp});

  const assetDashboardLink = (
    <span style={{marginLeft: 10}}>
      [<MetadataEntryLink to={to}>View Asset</MetadataEntryLink>]
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
                  {displayNameForAssetKey(assetKey)}
                  {assetDashboardLink}
                </>
              ),
            },
          ]}
          styles={{paddingBottom: 0}}
        />
        <MetadataEntries entries={metadataEntries} />
      </>
    </DefaultContent>
  );
};
