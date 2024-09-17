import {Box, NonIdealState, Spinner} from '@dagster-io/ui-components';
import React, {useMemo} from 'react';

import {BackfillLogsPageQuery, BackfillLogsPageQueryVariables} from './types/BackfillLogsTab.types';
import {BackfillDetailsBackfillFragment} from './types/useBackfillDetailsQuery.types';
import {gql} from '../../apollo-client';
import {QueryRefreshCountdown} from '../../app/QueryRefresh';
import {useCursorAccumulatedQuery} from '../../runs/useCursorAccumulatedQuery';
import {
  INSTIGATION_EVENT_LOG_FRAGMENT,
  InstigationEventLogTable,
} from '../../ticks/InstigationEventLogTable';
import {InstigationEventLogFragment} from '../../ticks/types/InstigationEventLogTable.types';

const getResultForBackfillLogsPage = (e: BackfillLogsPageQuery) => {
  if (e.partitionBackfillOrError.__typename === 'PartitionBackfill') {
    const {events, hasMore, cursor} = e.partitionBackfillOrError.logEvents;
    return {data: events, hasMore, cursor, error: undefined};
  } else {
    return {data: [], hasMore: false, error: e.partitionBackfillOrError, cursor: undefined};
  }
};

export const BackfillLogsTab = ({backfill}: {backfill: BackfillDetailsBackfillFragment}) => {
  const {
    error,
    fetched: events,
    refreshState,
  } = useCursorAccumulatedQuery<
    BackfillLogsPageQuery,
    BackfillLogsPageQueryVariables,
    InstigationEventLogFragment,
    {message: string}
  >({
    query: BACKFILL_LOGS_PAGE_QUERY,
    variables: useMemo(() => ({backfillId: backfill.id}), [backfill]),
    getResult: getResultForBackfillLogsPage,
  });

  const content = () => {
    if (error) {
      <Box flex={{justifyContent: 'center', alignItems: 'center'}} style={{flex: 1}}>
        <NonIdealState title="Unable to fetch logs" description={error.message} />
      </Box>;
    }
    if (events === null) {
      return (
        <Box flex={{justifyContent: 'center', alignItems: 'center'}} style={{flex: 1}}>
          <Spinner purpose="page" />
        </Box>
      );
    }
    if (events.length === 0) {
      return (
        <Box flex={{justifyContent: 'center', alignItems: 'center'}} style={{flex: 1}}>
          <NonIdealState
            title="No logs available"
            description="If backfill log storage is enabled, logs will appear as they are emitted by the backfill daemon."
          />
        </Box>
      );
    }
    return <InstigationEventLogTable events={events} />;
  };
  return (
    <>
      <div style={{position: 'absolute', right: 16, top: -32}}>
        <QueryRefreshCountdown refreshState={refreshState} />
      </div>
      {content()}
    </>
  );
};

export const BACKFILL_LOGS_PAGE_QUERY = gql`
  query BackfillLogsPageQuery($backfillId: String!, $cursor: String) {
    partitionBackfillOrError(backfillId: $backfillId) {
      __typename
      ... on PythonError {
        message
      }
      ... on BackfillNotFoundError {
        message
      }
      ... on PartitionBackfill {
        id
        logEvents(cursor: $cursor) {
          ... on InstigationEventConnection {
            cursor
            hasMore
            events {
              ...InstigationEventLog
            }
          }
        }
      }
    }
  }
  ${INSTIGATION_EVENT_LOG_FRAGMENT}
`;
