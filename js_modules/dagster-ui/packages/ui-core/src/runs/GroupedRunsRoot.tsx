import {
  Box,
  Button,
  ButtonLink,
  Colors,
  Icon,
  JoinedButtons,
  NonIdealState,
  Page,
  Tabs,
  TextInput,
  tokenToString,
} from '@dagster-io/ui-components';
import groupBy from 'lodash/groupBy';
import partition from 'lodash/partition';
import {useCallback, useLayoutEffect, useMemo} from 'react';

import {GroupedRunTable} from './GroupedRunTable';
import {QueuedRunsBanners} from './QueuedRunsBanners';
import {useSelectedRunsTab} from './RunListTabs';
import {failedStatuses, inProgressStatuses, queuedStatuses} from './RunStatuses';
import {DagsterTag} from './RunTag';
import {RunsQueryRefetchContext} from './RunUtils';
import {
  RunFilterToken,
  RunFilterTokenType,
  runsFilterForSearchTokens,
  useQueryPersistedRunFilters,
  useRunsFilterInput,
} from './RunsFilterInput';
import {TerminateAllRunsButton} from './TerminateAllRunsButton';
import {RunTableRunFragment} from './types/RunTable.types';
import {RunsRootQuery, RunsRootQueryVariables} from './types/RunsRoot.types';
import {AccumulatingFetchResult, useCursorAccumulatedQuery} from './useCursorAccumulatedQuery';
import {RUNS_ROOT_QUERY} from './usePaginatedRunsTableRuns';
import {QueryRefreshCountdown} from '../app/QueryRefresh';
import {useTrackPageView} from '../app/analytics';
import {RunStatus, RunsFilter} from '../graphql/types';
import {usePortalSlot} from '../hooks/usePortalSlot';
import {useQueryPersistedState} from '../hooks/useQueryPersistedState';
import {usePageLoadTrace} from '../performance';
import {LoadingSpinner} from '../ui/Loading';
import {StickyTableContainer} from '../ui/StickyTableContainer';
import {TabLink} from '../ui/TabLink';

const getResultFromRuns = (
  data: RunsRootQuery,
): AccumulatingFetchResult<RunTableRunFragment, string, any> => {
  if (data.pipelineRunsOrError.__typename !== 'Runs') {
    return {error: data.pipelineRunsOrError, cursor: undefined, hasMore: false, data: []};
  }
  const results = data.pipelineRunsOrError.results;
  return {
    data: results,
    hasMore: results.length === 30,
    cursor: results[results.length - 1]?.id,
    error: undefined,
  };
};

export type RunGrouping = {
  key: string;
  runs: RunTableRunFragment[];
  creationTime: number;
};

const groupKeyForRun = (run: RunTableRunFragment): string => {
  const tags = Object.fromEntries(run.tags.map((t) => [t.key, t.value]));
  return (
    tags[DagsterTag.Backfill] ||
    `${tags[DagsterTag.ScheduleName]}-${tags[DagsterTag.TickId]}` ||
    `${tags[DagsterTag.SensorName]}-${tags[DagsterTag.TickId]}` ||
    run.rootRunId ||
    run.id
  );
};

export function useGroupedRunsTableRuns(filter: RunsFilter) {
  const {fetched, error, refreshState} = useCursorAccumulatedQuery<
    RunsRootQuery,
    RunsRootQueryVariables,
    RunTableRunFragment
  >({
    query: RUNS_ROOT_QUERY,
    variables: {filter, limit: 30},
    getResult: getResultFromRuns,
  });

  const groups: RunGrouping[] | null = useMemo(() => {
    return fetched
      ? Object.entries(groupBy(fetched, groupKeyForRun))
          .map(([key, _runs]) => {
            const runs = _runs.sort((a, b) => a.creationTime - b.creationTime);
            return {
              key,
              runs,
              creationTime: runs[0]!.creationTime,
            };
          })
          .sort((a, b) => b.creationTime - a.creationTime)
      : null;
  }, [fetched]);

  return {groups, error, refreshState};
}

export const GroupedRunsRoot = () => {
  useTrackPageView();
  const trace = usePageLoadTrace('GroupedRunsRoot');

  const [filterTokens, setFilterTokens] = useQueryPersistedRunFilters();
  const filter = runsFilterForSearchTokens(filterTokens);

  const {groups, error, refreshState} = useGroupedRunsTableRuns(filter);

  const countQueued = groups?.filter((g) => g.runs.some((r) => r.status === RunStatus.QUEUED))
    .length;
  const countInProgress = groups?.filter((g) =>
    g.runs.some((r) => inProgressStatuses.has(r.status)),
  ).length;
  const countFailed = groups?.filter((g) => g.runs.some((r) => failedStatuses.has(r.status)))
    .length;

  // useBlockTraceOnQueryResult(queryResult, 'RunsRootQuery');

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

  const {button, activeFiltersJsx} = useRunsFilterInput({
    tokens: mutableTokens,
    onChange: setFilterTokensWithStatus,
    enabledFilters,
  });

  const [filtersPortal, filtersSlot] = usePortalSlot(button);
  const [offset, setOffset] = useQueryPersistedState<string>({queryKey: 'offset'});
  const offsetIdx = offset && groups ? groups?.findIndex((g) => g.key === offset) : 0;
  const page = groups ? groups.slice(offsetIdx, offsetIdx + 30) : null;
  const pageNumber = 1 + Math.floor(offsetIdx / 30);
  const pageCount = groups ? Math.ceil(groups.length / 30) : 0;

  function actionBar() {
    return (
      <Box style={{width: '100%', marginRight: 8}} flex={{justifyContent: 'space-between'}}>
        <Box flex={{direction: 'row', alignItems: 'center', gap: 8}}>{filtersSlot}</Box>
        <JoinedButtons>
          <Button
            icon={<Icon name="arrow_back" />}
            disabled={offsetIdx === 0}
            onClick={() => {
              if (!groups || !groups.length) {
                return;
              }
              setOffset(groups[Math.max(offsetIdx - 30, 0)]!.key);
            }}
          />
          <TextInput
            value={pageNumber}
            rightElement={<span>{` of ${pageCount}`}</span>}
            style={{width: 70, borderRadius: 0, height: 30}}
            onChange={(e) => {
              if (!groups) {
                return;
              }
              const pageIdx = Number(e.target.value) - 1;
              const offsetIdx = Math.max(0, Math.min(groups.length - 1, pageIdx * 30));
              setOffset(groups[offsetIdx]!.key);
            }}
          />
          <Button
            rightIcon={<Icon name="arrow_forward" />}
            disabled={!groups || groups.length <= offsetIdx + 30}
            onClick={() => {
              if (!groups || !groups.length) {
                return;
              }
              setOffset(groups[Math.min(offsetIdx + 30, groups.length - 1)]!.key);
            }}
          />
        </JoinedButtons>{' '}
        {currentTab === 'queued' ? (
          <TerminateAllRunsButton
            refetch={refreshState.refetch}
            filter={{...filter, statuses: Array.from(queuedStatuses)}}
            disabled={countQueued === 0}
          />
        ) : currentTab === 'in-progress' ? (
          <TerminateAllRunsButton
            refetch={refreshState.refetch}
            filter={{...filter, statuses: Array.from(inProgressStatuses)}}
            disabled={countInProgress === 0}
          />
        ) : undefined}
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
    if (page === null) {
      return <LoadingSpinner purpose="page" />;
    }

    return (
      <>
        <RunsRootPerformanceEmitter trace={trace} />
        <StickyTableContainer $top={0}>
          <GroupedRunTable
            groups={page}
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
            <TabLink id="all" title="All runs" to="/run-requests" />
            <TabLink id="queued" title={`Queued (${countQueued})`} to="/run-requests" />
            <TabLink
              id="in-progress"
              title={`In progress (${countInProgress})`}
              to="/run-requests"
            />
            <TabLink id="failed" title={`Failed (${countFailed})`} to="/run-requests" />
          </Tabs>
          <Box padding={{vertical: 16}}>
            <QueryRefreshCountdown refreshState={refreshState} />
          </Box>
        </Box>
      </Box>
      {filtersPortal}
      <RunsQueryRefetchContext.Provider value={{refetch: refreshState.refetch}}>
        {content()}
      </RunsQueryRefetchContext.Provider>
    </Page>
  );
};

const RunsRootPerformanceEmitter = ({trace}: {trace: ReturnType<typeof usePageLoadTrace>}) => {
  useLayoutEffect(() => {
    trace.endTrace();
  }, [trace]);
  return null;
};

// Imported via React.lazy, which requires a default export.
// eslint-disable-next-line import/no-default-export
export default GroupedRunsRoot;
