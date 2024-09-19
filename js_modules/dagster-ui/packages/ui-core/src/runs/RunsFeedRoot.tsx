import {Box, Colors, CursorHistoryControls, NonIdealState, Tabs} from '@dagster-io/ui-components';
import {useVirtualizer} from '@tanstack/react-virtual';
import {useMemo, useRef} from 'react';

import {RunBulkActionsMenu} from './RunActionsMenu';
import {RunsQueryRefetchContext} from './RunUtils';
import {RUNS_FEED_TABLE_ENTRY_FRAGMENT, RunsFeedRow, RunsFeedTableHeader} from './RunsFeedRow';
import {RunsFeedRootQuery, RunsFeedRootQueryVariables} from './types/RunsFeedRoot.types';
import {RunsFeedTableEntryFragment_Run} from './types/RunsFeedRow.types';
import {useCursorPaginatedQuery} from './useCursorPaginatedQuery';
import {gql} from '../apollo-client';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {
  FIFTEEN_SECONDS,
  QueryRefreshCountdown,
  useQueryRefreshAtInterval,
} from '../app/QueryRefresh';
import {useTrackPageView} from '../app/analytics';
import {useSelectionReducer} from '../hooks/useSelectionReducer';
import {CheckAllBox} from '../ui/CheckAllBox';
import {LoadingSpinner} from '../ui/Loading';
import {TabLink} from '../ui/TabLink';
import {Container, Inner, Row} from '../ui/VirtualizedTable';

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

  const parentRef = useRef<HTMLDivElement | null>(null);

  const entryIds = useMemo(() => entries.map((e) => e.id), [entries]);
  const [{checkedIds}, {onToggleFactory, onToggleAll}] = useSelectionReducer(entryIds);

  const rowVirtualizer = useVirtualizer({
    count: entries.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 84,
    overscan: 15,
  });

  const totalHeight = rowVirtualizer.getTotalSize();
  const items = rowVirtualizer.getVirtualItems();

  function actionBar() {
    return (
      <Box flex={{justifyContent: 'space-between'}} style={{width: '100%'}}>
        <Box>{/** filters */}</Box>
        <Box flex={{gap: 12}} style={{marginRight: 8}}>
          <CursorHistoryControls {...paginationProps} style={{marginTop: 0}} />
          <RunBulkActionsMenu
            clearSelection={() => onToggleAll(false)}
            selected={entries.filter(
              (e): e is RunsFeedTableEntryFragment_Run =>
                checkedIds.has(e.id) && e.__typename === 'Run',
            )}
          />
        </Box>
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
      <div style={{overflow: 'hidden'}}>
        <Container ref={parentRef}>
          <RunsFeedTableHeader
            checkbox={
              <CheckAllBox
                checkedCount={checkedIds.size}
                totalCount={entries.length}
                onToggleAll={onToggleAll}
              />
            }
          />
          <Inner $totalHeight={totalHeight}>
            {items.map(({index, size, start, key}) => {
              const entry = entries[index];
              if (!entry) {
                return <span key={key} />;
              }
              return (
                <Row $height={size} $start={start} data-key={key} key={key}>
                  <div ref={rowVirtualizer.measureElement} data-index={index}>
                    <RunsFeedRow
                      key={key}
                      entry={entry}
                      checked={checkedIds.has(entry.id)}
                      onToggleChecked={onToggleFactory(entry.id)}
                      refetch={refreshState.refetch}
                    />
                  </div>
                </Row>
              );
            })}
          </Inner>
        </Container>
      </div>
    );
  };

  return (
    <Box flex={{direction: 'column'}} style={{height: '100%', overflow: 'hidden'}}>
      <Box
        border="bottom"
        background={Colors.backgroundLight()}
        padding={{left: 24, right: 20, top: 12}}
        flex={{direction: 'row', justifyContent: 'space-between'}}
      >
        <Tabs selectedTabId="all">
          <TabLink id="all" title="All runs" to="/runs-feed" />
          {/* <TabLink id="queued" title={`Queued (${countQueued})`} to="/runs-feed" />
            <TabLink id="in-progress" title={`In progress (${countInProgress})`} to="/runs-feed" />
            <TabLink id="failed" title={`Failed (${countFailed})`} to="/runs-feed" /> */}
        </Tabs>
        <Box flex={{gap: 16, alignItems: 'center'}}>
          <QueryRefreshCountdown refreshState={refreshState} />
        </Box>
      </Box>

      <Box flex={{direction: 'column', gap: 32}} padding={{vertical: 12, left: 24, right: 12}}>
        {actionBar()}
      </Box>

      {/* {filtersPortal} */}
      <RunsQueryRefetchContext.Provider value={{refetch: refreshState.refetch}}>
        {content()}
      </RunsQueryRefetchContext.Provider>
    </Box>
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
