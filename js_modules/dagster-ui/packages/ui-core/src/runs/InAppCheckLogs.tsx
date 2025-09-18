import {Box, NonIdealState, Spinner} from '@dagster-io/ui-components';
import {useMemo} from 'react';
import {useParams} from 'react-router-dom';

import {gql} from '../apollo-client';
import {QueryRefreshCountdown} from '../app/QueryRefresh';
import {useCursorAccumulatedQuery} from '../runs/useCursorAccumulatedQuery';
import {
  INSTIGATION_EVENT_LOG_FRAGMENT,
  InstigationEventLogTable,
} from '../ticks/InstigationEventLogTable';
import {
  AssetCheckLogsPageQuery,
  AssetCheckLogsPageQueryVariables,
} from './types/InAppCheckLogs.types';
import {InstigationEventLogFragment} from '../ticks/types/InstigationEventLogTable.types';

const getResultForAssetCheckLogsPage = (e: AssetCheckLogsPageQuery) => {
  if (e.assetChecklogEvents.__typename === 'InstigationEventConnection') {
    const {events, hasMore, cursor} = e.assetChecklogEvents;
    return {data: events, hasMore, cursor, error: undefined};
  } else {
    return {data: [], hasMore: false, error: {message: 'Unknown error'}, cursor: undefined};
  }
};

export const InAppCheckLogs = () => {
  const {runId, checkKey} = useParams<{runId: string; checkKey: string}>();
  const {
    error,
    fetched: events,
    refreshState,
  } = useCursorAccumulatedQuery<
    AssetCheckLogsPageQuery,
    AssetCheckLogsPageQueryVariables,
    InstigationEventLogFragment,
    {message: string}
  >({
    query: ASSET_CHECK_LOGS_PAGE_QUERY,
    variables: useMemo(() => ({runId, checkKey}), [runId, checkKey]),
    getResult: getResultForAssetCheckLogsPage,
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

// Imported via React.lazy, which requires a default export.
// eslint-disable-next-line import/no-default-export
export default InAppCheckLogs;

export const ASSET_CHECK_LOGS_PAGE_QUERY = gql`
  query AssetCheckLogsPageQuery($runId: String!, $checkKey: String!, $cursor: String) {
    assetChecklogEvents(runId: $runId, checkKey: $checkKey, cursor: $cursor) {
      __typename
      ... on InstigationEventConnection {
        cursor
        hasMore
        events {
          ...InstigationEventLog
        }
      }
    }
  }
  ${INSTIGATION_EVENT_LOG_FRAGMENT}
`;
