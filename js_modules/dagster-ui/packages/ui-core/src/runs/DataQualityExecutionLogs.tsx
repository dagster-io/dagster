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
  DataQualityExecutionLogsQueryVariables,
  DataQualityExecutionLogsQuery,
} from './types/DataQualityExecutionLogs.types';
import {InstigationEventLogFragment} from '../ticks/types/InstigationEventLogTable.types';

const getResultForDataQualityExecutionLogsPage = (e: DataQualityExecutionLogsQuery) => {
  if (e.dataQualityExecutionLogs.__typename === 'InstigationEventConnection') {
    const {events, hasMore, cursor} = e.dataQualityExecutionLogs;
    return {data: events, hasMore, cursor, error: undefined};
  } else {
    return {data: [], hasMore: false, error: {message: 'Unknown error'}, cursor: undefined};
  }
};

export const DataQualityExecutionLogs = () => {
  const {executionId, checkName} = useParams<{executionId: string; checkName: string}>();
  const {
    error,
    fetched: events,
    refreshState,
  } = useCursorAccumulatedQuery<
    DataQualityExecutionLogsQuery,
    DataQualityExecutionLogsQueryVariables,
    InstigationEventLogFragment,
    {message: string}
  >({
    query: DATA_QUALITY_EXECUTION_LOGS_QUERY,
    variables: useMemo(() => ({executionId, checkName, cursor: undefined}), [executionId, checkName]),
    getResult: getResultForDataQualityExecutionLogsPage,
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
export default DataQualityExecutionLogs;


export const DATA_QUALITY_EXECUTION_LOGS_QUERY = gql`
  query DataQualityExecutionLogsQuery($executionId: String!, $checkName: String!, $cursor: String) {
    dataQualityExecutionLogs(executionId: $executionId, checkName: $checkName, cursor: $cursor) {
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