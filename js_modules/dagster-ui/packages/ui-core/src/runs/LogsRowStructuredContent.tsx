// eslint-disable-next-line no-restricted-imports
import {Intent} from '@blueprintjs/core';
import {Box, Colors, Tag} from '@dagster-io/ui-components';
import qs from 'qs';
import * as React from 'react';
import {Link, useLocation} from 'react-router-dom';

import {EventTypeColumn} from './LogsRowComponents';
import {IRunMetadataDict} from './RunMetadataProvider';
import {eventTypeToDisplayType} from './getRunFilterProviders';
import {
  LogsRowStructuredFragment,
  LogsRowStructuredFragment_AssetCheckEvaluationEvent,
} from './types/LogsRow.types';
import {assertUnreachable} from '../app/Util';
import {PythonErrorFragment} from '../app/types/PythonErrorFragment.types';
import {displayNameForAssetKey} from '../asset-graph/Utils';
import {
  assetDetailsPathForAssetCheck,
  assetDetailsPathForKey,
} from '../assets/assetDetailsPathForKey';
import {AssetKey} from '../assets/types';
import {DagsterEventType, ErrorSource} from '../graphql/types';
import {
  LogRowStructuredContentTable,
  MetadataEntries,
  MetadataEntryLink,
} from '../metadata/MetadataEntry';
import {MetadataEntryFragment} from '../metadata/types/MetadataEntryFragment.types';

interface IStructuredContentProps {
  node: LogsRowStructuredFragment;
  metadata: IRunMetadataDict;
}

export const LogsRowStructuredContent = ({node, metadata}: IStructuredContentProps) => {
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
          logType: 'stderr',
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
      return <DefaultContent eventType={eventType} message={node.message} />;
    case 'AlertFailureEvent':
      return <DefaultContent eventType={eventType} message={node.message} eventIntent="warning" />;
    case 'ResourceInitFailureEvent':
    case 'RunCanceledEvent':
    case 'RunFailureEvent':
      if (node.error) {
        return <FailureContent message={node.message} error={node.error} eventType={eventType} />;
      }
      return <DefaultContent message={node.message} eventType={eventType} eventIntent="danger" />;
    case 'RunSuccessEvent':
      return <DefaultContent message={node.message} eventType={eventType} eventIntent="success" />;
    case 'RunStartEvent':
    case 'RunEnqueuedEvent':
    case 'RunDequeuedEvent':
    case 'RunStartingEvent':
    case 'RunCancelingEvent':
    case 'ResourceInitStartedEvent':
    case 'ResourceInitSuccessEvent':
    case 'StepWorkerStartedEvent':
    case 'StepWorkerStartingEvent':
      return <DefaultContent message={node.message} eventType={eventType} />;
    case 'EngineEvent':
      if (node.error) {
        return (
          <FailureContent
            message={node.message}
            error={node.error}
            metadataEntries={node.metadataEntries}
            eventType={eventType}
          />
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
      const updatedQuery = {...currentQuery, logType: 'stderr', logFileKey: node.fileKey};
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
    case 'AssetCheckEvaluationPlannedEvent':
      return <DefaultContent message={node.message} eventType={eventType} />;
    case 'AssetCheckEvaluationEvent':
      return <AssetCheckEvaluationContent node={node} eventType={eventType} />;
    default:
      // This allows us to check that the switch is exhaustive because the union type should
      // have been narrowed following each successive case to `never` at this point.
      return assertUnreachable(node);
  }
};

// Structured Content Renderers

const DefaultContent = ({
  message,
  eventType,
  eventColor,
  eventIntent,
  children,
}: {
  message: string;
  eventType?: string;
  eventColor?: string;
  eventIntent?: Intent;
  metadataEntries?: MetadataEntryFragment[];
  children?: React.ReactElement;
}) => {
  return (
    <>
      <EventTypeColumn>
        {eventType && (
          <Tag
            intent={eventIntent}
            style={
              eventColor
                ? {
                    fontSize: '12px',
                    color: 'black',
                    background: eventColor,
                  }
                : {
                    fontSize: '12px',
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

const FailureContent = ({
  message,
  error,
  errorSource,
  eventType,
  metadataEntries,
}: {
  message?: string;
  eventType: string;
  error?: PythonErrorFragment | null;
  errorSource?: ErrorSource | null;
  metadataEntries?: MetadataEntryFragment[];
}) => {
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
    errorMessage = <span style={{color: Colors.textRed()}}>{`${error.message}`}</span>;

    // omit the outer stack for user code errors with a cause
    // as the outer stack is just framework code
    if (
      error.stack.length &&
      !(errorSource === ErrorSource.USER_CODE_ERROR && error.errorChain.length)
    ) {
      errorStack = (
        <span style={{color: Colors.textRed()}}>{`\nStack Trace:\n${error.stack}`}</span>
      );
    }

    if (error.errorChain.length) {
      errorCause = error.errorChain.map((chainLink, index) => (
        <React.Fragment key={index}>
          {chainLink.isExplicitLink
            ? `The above exception was caused by the following exception:\n`
            : `The above exception occurred during handling of the following exception:\n`}
          <span style={{color: Colors.textRed()}}>{`${chainLink.error.message}`}</span>
          {chainLink.error.stack.length ? (
            <span
              style={{color: Colors.textRed()}}
            >{`\nStack Trace:\n${chainLink.error.stack}`}</span>
          ) : null}
        </React.Fragment>
      ));
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

const StepUpForRetryContent = ({
  message,
  error,
}: {
  message?: string;
  error?: PythonErrorFragment | null;
}) => {
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
    if (!error.errorChain.length) {
      errorMessage = <span style={{color: Colors.textRed()}}>{`${error.message}`}</span>;
      errorStack = (
        <span style={{color: Colors.textRed()}}>{`\nStack Trace:\n${error.stack}`}</span>
      );
    } else {
      // If there is a cause, this was a different exception. Show that instead.
      errorCause = (
        <>
          {error.errorChain.map((chainLink, index) => (
            <React.Fragment key={index}>
              {index === 0
                ? `The retry request was caused by the following exception:\n`
                : `The above exception was caused by the following exception:\n`}
              <span style={{color: Colors.textRed()}}>{`${chainLink.error.message}`}</span>
              <span
                style={{color: Colors.textRed()}}
              >{`\nStack Trace:\n${chainLink.error.stack}`}</span>
            </React.Fragment>
          ))}
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

const AssetCheckEvaluationContent = ({
  node,
  eventType,
}: {
  node: LogsRowStructuredFragment_AssetCheckEvaluationEvent;
  eventType: string;
}) => {
  const {checkName, success, metadataEntries, targetMaterialization, assetKey} = node.evaluation;

  const checkLink = assetDetailsPathForAssetCheck({assetKey, name: checkName});

  // Target materialization timestamp is in seconds, and must be converted to msec for the query param.
  const asOf = targetMaterialization?.timestamp ?? null;
  const matLink = assetDetailsPathForKey(assetKey, {
    view: 'events',
    asOf: asOf ? `${Math.floor(asOf * 1000)}` : undefined,
  });

  return (
    <DefaultContent
      message=""
      eventType={eventType}
      eventIntent={success ? Intent.SUCCESS : Intent.DANGER}
    >
      <div>
        <div style={{color: success ? 'inherit' : Colors.textRed()}}>
          Check <MetadataEntryLink to={checkLink}>{checkName}</MetadataEntryLink>
          {` ${success ? 'succeeded' : 'failed'} for materialization of `}
          <MetadataEntryLink to={matLink}>{displayNameForAssetKey(assetKey)}</MetadataEntryLink>.
        </div>
        <MetadataEntries entries={metadataEntries} />
      </div>
    </DefaultContent>
  );
};

const AssetMetadataContent = ({
  message,
  assetKey,
  metadataEntries,
  eventType,
  timestamp,
}: {
  message: string;
  assetKey: AssetKey | null;
  metadataEntries: MetadataEntryFragment[];
  eventType: string;
  timestamp: string;
}) => {
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
          styles={metadataEntries?.length ? {paddingBottom: 0} : {}}
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
        />
        <MetadataEntries entries={metadataEntries} />
      </>
    </DefaultContent>
  );
};
