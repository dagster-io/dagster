import {
  Box,
  ButtonLink,
  CursorHistoryControls,
  Heading,
  NonIdealState,
  Page,
  PageHeader,
  tokenToString,
} from '@dagster-io/ui-components';
import partition from 'lodash/partition';
import {useCallback, useMemo} from 'react';

import {QueuedRunsBanners} from './QueuedRunsBanners';
import {useRunListTabs, useSelectedRunsTab} from './RunListTabs';
import {inProgressStatuses, queuedStatuses} from './RunStatuses';
import {RunTable} from './RunTable';
import {RunsQueryRefetchContext} from './RunUtils';
import {
  RunFilterToken,
  RunFilterTokenType,
  runsFilterForSearchTokens,
  useQueryPersistedRunFilters,
  useRunsFilterInput,
} from './RunsFilterInput';
import {TerminateAllRunsButton} from './TerminateAllRunsButton';
import {usePaginatedRunsTableRuns} from './usePaginatedRunsTableRuns';
import {ApolloError} from '../apollo-client';
import {
  FIFTEEN_SECONDS,
  QueryRefreshCountdown,
  useMergedRefresh,
  useQueryRefreshAtInterval,
} from '../app/QueryRefresh';
import {useTrackPageView} from '../app/analytics';
import {usePortalSlot} from '../hooks/usePortalSlot';
import {Loading} from '../ui/Loading';
import {StickyTableContainer} from '../ui/StickyTableContainer';

const PAGE_SIZE = 25;

export const RunsRoot = () => {
  useTrackPageView();

  const [filterTokens, setFilterTokens] = useQueryPersistedRunFilters();
  const filter = runsFilterForSearchTokens(filterTokens);
  const {queryResult, paginationProps} = usePaginatedRunsTableRuns(filter, PAGE_SIZE);

  const refreshState = useQueryRefreshAtInterval(queryResult, FIFTEEN_SECONDS);

  const currentTab = useSelectedRunsTab(filterTokens);
  const staticStatusTags = currentTab !== 'all';
  const [statusTokens, nonStatusTokens] = partition(
    filterTokens,
    (token) => token.token === 'status',
  );

  const setFilterTokensWithStatus = useCallback(
    (tokens: RunFilterToken[]) => {
      if (staticStatusTags) {
        setFilterTokens([...statusTokens, ...tokens]);
      } else {
        setFilterTokens(tokens);
      }
    },
    [setFilterTokens, staticStatusTags, statusTokens],
  );

  const onAddTag = useCallback(
    (token: RunFilterToken) => {
      const tokenAsString = tokenToString(token);
      if (!nonStatusTokens.some((token) => tokenToString(token) === tokenAsString)) {
        setFilterTokensWithStatus([...nonStatusTokens, token]);
      }
    },
    [nonStatusTokens, setFilterTokensWithStatus],
  );

  const enabledFilters = useMemo(() => {
    const filters: RunFilterTokenType[] = [
      'tag',
      'snapshotId',
      'id',
      'job',
      'pipeline',
      'partition',
      'backfill',
    ];

    if (!staticStatusTags) {
      filters.push('status');
    }

    return filters;
  }, [staticStatusTags]);

  const mutableTokens = useMemo(() => {
    if (staticStatusTags) {
      return filterTokens.filter((token) => token.token !== 'status');
    }
    return filterTokens;
  }, [filterTokens, staticStatusTags]);

  const {tabs, queryResult: runQueryResult} = useRunListTabs(filter);
  const countRefreshState = useQueryRefreshAtInterval(runQueryResult, FIFTEEN_SECONDS);
  const combinedRefreshState = useMergedRefresh(countRefreshState, refreshState);

  const {button, activeFiltersJsx} = useRunsFilterInput({
    tokens: mutableTokens,
    onChange: setFilterTokensWithStatus,
    enabledFilters,
  });

  const [filtersPortal, filtersSlot] = usePortalSlot(button);

  function actionBar() {
    return (
      <Box style={{width: '100%', marginRight: 8}} flex={{justifyContent: 'space-between'}}>
        <Box flex={{direction: 'row', alignItems: 'center', gap: 8}}>
          {tabs}
          {filtersSlot}
        </Box>
        {currentTab === 'queued' ? (
          <TerminateAllRunsButton
            refetch={combinedRefreshState.refetch}
            filter={{...filter, statuses: Array.from(queuedStatuses)}}
            disabled={
              runQueryResult.data?.queuedCount.__typename === 'Runs'
                ? runQueryResult.data?.queuedCount.count === 0
                : true
            }
          />
        ) : currentTab === 'in-progress' ? (
          <TerminateAllRunsButton
            refetch={combinedRefreshState.refetch}
            filter={{...filter, statuses: Array.from(inProgressStatuses)}}
            disabled={
              runQueryResult.data?.inProgressCount.__typename === 'Runs'
                ? runQueryResult.data?.inProgressCount.count === 0
                : true
            }
          />
        ) : undefined}
      </Box>
    );
  }

  return (
    <Page>
      <PageHeader
        title={<Heading>Runs</Heading>}
        right={<QueryRefreshCountdown refreshState={combinedRefreshState} />}
      />
      {filtersPortal}
      <RunsQueryRefetchContext.Provider value={{refetch: queryResult.refetch}}>
        <Loading
          queryResult={queryResult}
          allowStaleData
          renderError={(error: ApolloError) => {
            // In this case, a 400 is most likely due to invalid run filters, which are a GraphQL
            // validation error but surfaced as a 400.
            const badRequest = !!(
              error?.networkError &&
              'statusCode' in error.networkError &&
              error.networkError.statusCode === 400
            );
            return (
              <Box flex={{direction: 'column', gap: 32}} padding={{vertical: 8, horizontal: 24}}>
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
          }}
        >
          {({pipelineRunsOrError}) => {
            if (pipelineRunsOrError.__typename !== 'Runs') {
              return (
                <Box padding={{vertical: 64}}>
                  <NonIdealState
                    icon="error"
                    title="Query Error"
                    description={pipelineRunsOrError.message}
                  />
                </Box>
              );
            }

            return (
              <>
                <StickyTableContainer $top={0}>
                  <RunTable
                    runs={pipelineRunsOrError.results}
                    onAddTag={onAddTag}
                    filter={filter}
                    actionBarComponents={actionBar()}
                    belowActionBarComponents={
                      currentTab === 'queued' || activeFiltersJsx.length ? (
                        <>
                          {currentTab === 'queued' && <QueuedRunsBanners />}
                          {activeFiltersJsx.length > 0 && (
                            <>
                              {activeFiltersJsx}
                              <ButtonLink onClick={() => setFilterTokensWithStatus([])}>
                                Clear all
                              </ButtonLink>
                            </>
                          )}
                        </>
                      ) : null
                    }
                  />
                </StickyTableContainer>
                {pipelineRunsOrError.results.length > 0 ? (
                  <div style={{marginTop: '16px'}}>
                    <CursorHistoryControls {...paginationProps} />
                  </div>
                ) : null}
              </>
            );
          }}
        </Loading>
      </RunsQueryRefetchContext.Provider>
    </Page>
  );
};

// Imported via React.lazy, which requires a default export.
// eslint-disable-next-line import/no-default-export
export default RunsRoot;
