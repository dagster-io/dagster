import {gql} from '@apollo/client';
import {
  Box,
  Colors,
  CursorHistoryControls,
  NonIdealState,
  Page,
  Tabs,
} from '@dagster-io/ui-components';
import {PYTHON_ERROR_FRAGMENT} from 'shared/app/PythonErrorFragment';

import {RunsQueryRefetchContext} from './RunUtils';
import {RUNS_FEED_TABLE_ENTRY_FRAGMENT, RunsFeedTable} from './RunsFeedTable';
import {RunsFeedRootQuery, RunsFeedRootQueryVariables} from './types/RunsFeedRoot.types';
import {useCursorPaginatedQuery} from './useCursorPaginatedQuery';
import {
  FIFTEEN_SECONDS,
  QueryRefreshCountdown,
  useQueryRefreshAtInterval,
} from '../app/QueryRefresh';
import {useTrackPageView} from '../app/analytics';
import {LoadingSpinner} from '../ui/Loading';
import {StickyTableContainer} from '../ui/StickyTableContainer';
import {TabLink} from '../ui/TabLink';

const PAGE_SIZE = 25;

export function useRunsFeedEntries() {
  const {queryResult, paginationProps} = useCursorPaginatedQuery<
    RunsFeedRootQuery,
    RunsFeedRootQueryVariables
  >({
    query: RUNS_FEED_ROOT_QUERY,
    pageSize: PAGE_SIZE,
    variables: {
      // filters here?
    },
    nextCursorForResult: (runs) => {
      if (runs.runsFeedOrError.__typename !== 'RunsFeedConnection') {
        return undefined;
      }
      return runs.runsFeedOrError.hasMore ? runs.runsFeedOrError.cursor : undefined;
    },
    getResultArray: (data) => {
      if (!data || data.runsFeedOrError.__typename !== 'RunsFeedConnection') {
        return [];
      }
      return data.runsFeedOrError.results;
    },
  });

  const entries =
    queryResult.data?.runsFeedOrError.__typename === 'RunsFeedConnection'
      ? queryResult.data?.runsFeedOrError.results
      : [];

  return {queryResult, paginationProps, entries};
}

export const RunsFeedRoot = () => {
  useTrackPageView();

  const {entries, paginationProps, queryResult} = useRunsFeedEntries();
  const refreshState = useQueryRefreshAtInterval(queryResult, FIFTEEN_SECONDS);
  const {error} = queryResult;

  function actionBar() {
    return (
      <Box style={{width: '100%', marginRight: 8}} flex={{justifyContent: 'space-between'}}>
        <Box flex={{gap: 8}}>{/**options */}</Box>
        <CursorHistoryControls {...paginationProps} style={{marginTop: 0}} />
      </Box>
    );
  }

  const content = () => {
    if (error) {
      // In this case, a 400 is most likely due to invalid run filters, which are a GraphQL
      // validation error but surfaced as a 400.
      const badRequest = !!(
        typeof error === 'object' &&
        'statusCode' in error &&
        error.statusCode === 400
      );
      return (
        <Box flex={{direction: 'column', gap: 32}} padding={{vertical: 8, left: 24, right: 12}}>
          {actionBar()}
          <NonIdealState
            icon="warning"
            title={badRequest ? 'Invalid run filters' : 'Unexpected error'}
            description={
              badRequest
                ? 'The specified run filters are not valid. Please check the filters and try again.'
                : 'An unexpected error occurred. Check the console for details.'
            }
          />
        </Box>
      );
    }
    if (queryResult.loading && !queryResult.data) {
      return <LoadingSpinner purpose="page" />;
    }

    return (
      <>
        <StickyTableContainer $top={0}>
          <RunsFeedTable
            entries={entries}
            refetch={refreshState.refetch}
            actionBarComponents={actionBar()}
            belowActionBarComponents={null}
          />
        </StickyTableContainer>
      </>
    );
  };

  return (
    <Page>
      <Box
        background={Colors.backgroundLight()}
        padding={{left: 24, right: 12, top: 12}}
        border="bottom"
      >
        <Box flex={{direction: 'row', justifyContent: 'space-between'}}>
          <Tabs selectedTabId="all">
            <TabLink id="all" title="All runs" to="/runs-feed" />
            {/* <TabLink id="queued" title={`Queued (${countQueued})`} to="/runs-feed" />
            <TabLink id="in-progress" title={`In progress (${countInProgress})`} to="/runs-feed" />
            <TabLink id="failed" title={`Failed (${countFailed})`} to="/runs-feed" /> */}
          </Tabs>
          <Box padding={{vertical: 16}}>
            <QueryRefreshCountdown refreshState={refreshState} />
          </Box>
        </Box>
      </Box>
      {/* {filtersPortal} */}
      <RunsQueryRefetchContext.Provider value={{refetch: refreshState.refetch}}>
        {content()}
      </RunsQueryRefetchContext.Provider>
    </Page>
  );
};

// Imported via React.lazy, which requires a default export.
// eslint-disable-next-line import/no-default-export
export default RunsFeedRoot;

export const RUNS_FEED_ROOT_QUERY = gql`
  query RunsFeedRootQuery($limit: Int!, $cursor: String) {
    runsFeedOrError(limit: $limit, cursor: $cursor) {
      ... on RunsFeedConnection {
        cursor
        hasMore
        results {
          id
          ...RunsFeedTableEntryFragment
        }
      }
      ...PythonErrorFragment
    }
  }

  ${RUNS_FEED_TABLE_ENTRY_FRAGMENT}
  ${PYTHON_ERROR_FRAGMENT}
`;
