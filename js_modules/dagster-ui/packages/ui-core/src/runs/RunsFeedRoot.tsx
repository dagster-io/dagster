import {Box, Checkbox, Colors, tokenToString} from '@dagster-io/ui-components';
import partition from 'lodash/partition';
import {useCallback, useMemo} from 'react';

import {RunsQueryRefetchContext} from './RunUtils';
import {RunsFeedError} from './RunsFeedError';
import {RunsFeedTable} from './RunsFeedTable';
import {useRunsFeedTabs, useSelectedRunsFeedTab} from './RunsFeedTabs';
import {
  RunFilterToken,
  RunFilterTokenType,
  runsFilterForSearchTokens,
  useQueryPersistedRunFilters,
  useRunsFilterInput,
} from './RunsFilterInput';
import {ScheduledRunList} from './ScheduledRunListRoot';
import {useRunsFeedEntries} from './useRunsFeedEntries';
import {
  FIFTEEN_SECONDS,
  QueryRefreshCountdown,
  useMergedRefresh,
  useQueryRefreshAtInterval,
} from '../app/QueryRefresh';
import {useTrackPageView} from '../app/analytics';
import {RunsFeedView} from '../graphql/types';
import {useQueryPersistedState} from '../hooks/useQueryPersistedState';
import {Loading} from '../ui/Loading';

const filters: RunFilterTokenType[] = [
  'tag',
  'snapshotId',
  'id',
  'job',
  'pipeline',
  'partition',
  'backfill',
  'status',
];

export const RunsFeedRoot = () => {
  useTrackPageView();

  const [filterTokens, setFilterTokens] = useQueryPersistedRunFilters();
  const filter = runsFilterForSearchTokens(filterTokens);
  const [view, setView] = useQueryPersistedState<RunsFeedView>({
    queryKey: 'view',
    defaults: {view: RunsFeedView.ROOTS},
  });

  const currentTab = useSelectedRunsFeedTab(filterTokens, view);
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

  const mutableTokens = useMemo(() => {
    if (staticStatusTags) {
      return filterTokens.filter((token) => token.token !== 'status');
    }
    return filterTokens;
  }, [filterTokens, staticStatusTags]);

  const {button, activeFiltersJsx} = useRunsFilterInput({
    tokens: mutableTokens,
    onChange: setFilterTokensWithStatus,
    enabledFilters: filters,
  });

  const {tabs, queryResult: runQueryResult} = useRunsFeedTabs(filter, view);

  const {entries, paginationProps, queryResult, scheduledQueryResult} = useRunsFeedEntries(
    filter,
    currentTab,
    view,
  );
  const refreshState = useQueryRefreshAtInterval(
    currentTab === 'scheduled' ? scheduledQueryResult : queryResult,
    FIFTEEN_SECONDS,
  );
  const countRefreshState = useQueryRefreshAtInterval(runQueryResult, FIFTEEN_SECONDS);
  const combinedRefreshState = useMergedRefresh(countRefreshState, refreshState);
  const {error} = queryResult;

  const actionBarComponents = (
    <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
      {button}

      <Checkbox
        label={<span>Show runs within backfills</span>}
        checked={currentTab === 'queued' || view === RunsFeedView.RUNS}
        disabled={currentTab === 'queued' || currentTab === 'backfills'}
        onChange={() => {
          setView(view === RunsFeedView.RUNS ? RunsFeedView.ROOTS : RunsFeedView.RUNS);
        }}
      />
    </Box>
  );

  const belowActionBarComponents = activeFiltersJsx.length ? (
    <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>{activeFiltersJsx}</Box>
  ) : null;

  function content() {
    if (currentTab === 'scheduled') {
      return (
        <Loading queryResult={scheduledQueryResult} allowStaleData>
          {(result) => {
            return <ScheduledRunList result={result} />;
          }}
        </Loading>
      );
    }
    if (error) {
      return <RunsFeedError error={error} />;
    }

    return (
      <RunsFeedTable
        entries={entries}
        loading={queryResult.loading}
        onAddTag={onAddTag}
        refetch={combinedRefreshState.refetch}
        actionBarComponents={actionBarComponents}
        belowActionBarComponents={belowActionBarComponents}
        paginationProps={paginationProps}
        filter={filter}
      />
    );
  }

  return (
    <Box style={{height: '100%', display: 'grid', gridTemplateRows: 'auto minmax(0, 1fr)'}}>
      <Box
        border="bottom"
        background={Colors.backgroundLight()}
        padding={{left: 24, right: 20}}
        flex={{direction: 'row', justifyContent: 'space-between'}}
      >
        {tabs}
        <Box flex={{gap: 16, alignItems: 'center'}}>
          <QueryRefreshCountdown refreshState={combinedRefreshState} />
        </Box>
      </Box>
      <div>
        <RunsQueryRefetchContext.Provider value={{refetch: combinedRefreshState.refetch}}>
          {content()}
        </RunsQueryRefetchContext.Provider>
      </div>
    </Box>
  );
};

// Imported via React.lazy, which requires a default export.
// eslint-disable-next-line import/no-default-export
export default RunsFeedRoot;
