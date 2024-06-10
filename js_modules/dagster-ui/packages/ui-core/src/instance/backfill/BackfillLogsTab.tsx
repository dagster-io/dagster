import {gql} from '@apollo/client';
import {Box, NonIdealState, Spinner} from '@dagster-io/ui-components';
import React from 'react';

import {BackfillLogsPageQuery, BackfillLogsPageQueryVariables} from './types/BackfillLogsTab.types';
import {BackfillDetailsBackfillFragment} from './types/BackfillPage.types';
import {QueryRefreshCountdown} from '../../app/QueryRefresh';
import {useCursorAccumulatedQuery} from '../../runs/useCursorAccumulatedQuery';
import {
  INSTIGATION_EVENT_LOG_FRAGMENT,
  InstigationEventLogTable,
} from '../../ticks/InstigationEventLogTable';
import {InstigationEventLogFragment} from '../../ticks/types/InstigationEventLogTable.types';

const getResultsForBackfillLogsPage = (e?: BackfillLogsPageQuery) => {
  return e?.partitionBackfillOrError.__typename === 'PartitionBackfill'
    ? e.partitionBackfillOrError.logEvents.events
    : [];
};
const getFetchStateForBackfillLogsPage = (e?: BackfillLogsPageQuery) => {
  return e?.partitionBackfillOrError.__typename === 'PartitionBackfill'
    ? e.partitionBackfillOrError.logEvents
    : null;
};

export const BackfillLogsTab = ({backfill}: {backfill: BackfillDetailsBackfillFragment}) => {
  const {fetched: events, refreshState} = useCursorAccumulatedQuery<
    BackfillLogsPageQuery,
    BackfillLogsPageQueryVariables,
    InstigationEventLogFragment
  >({
    query: BACKFILL_LOGS_PAGE_QUERY,
    variables: {backfillId: backfill.id},
    getResultArray: getResultsForBackfillLogsPage,
    getNextFetchState: getFetchStateForBackfillLogsPage,
  });

  return (
    <>
      <div style={{position: 'absolute', right: 16, top: -32}}>
        <QueryRefreshCountdown refreshState={refreshState} />
      </div>
      {events === null ? (
        <Box flex={{justifyContent: 'center', alignItems: 'center'}} style={{flex: 1}}>
          <Spinner purpose="page" />
        </Box>
      ) : events.length > 0 ? (
        <InstigationEventLogTable events={events} />
      ) : (
        <Box flex={{justifyContent: 'center', alignItems: 'center'}} style={{flex: 1}}>
          <NonIdealState
            title="No logs available"
            description="If backfill log storage is enabled, logs will appear as they are emitted by the backfill daemon."
          />
        </Box>
      )}
    </>
  );
};

export const BACKFILL_LOGS_PAGE_QUERY = gql`
  query BackfillLogsPageQuery($backfillId: String!, $cursor: String) {
    partitionBackfillOrError(backfillId: $backfillId) {
      __typename
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
