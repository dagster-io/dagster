import {
  Box,
  Button,
  ButtonGroup,
  Colors,
  CursorHistoryControls,
  ErrorBoundary,
  NonIdealState,
  Spinner,
} from '@dagster-io/ui-components';
import React, {useDeferredValue, useMemo} from 'react';

import {ExecutionTimeline} from './ExecutionTimeline';
import {BackfillDetailsBackfillFragment} from './types/useBackfillDetailsQuery.types';
import {
  FIFTEEN_SECONDS,
  QueryRefreshCountdown,
  useQueryRefreshAtInterval,
} from '../../app/QueryRefresh';
import {RunsFilter} from '../../graphql/types';
import {useQueryPersistedState} from '../../hooks/useQueryPersistedState';
import {useTimelineRange} from '../../overview/OverviewTimelineRoot';
import {RunTable} from '../../runs/RunTable';
import {DagsterTag} from '../../runs/RunTag';
import {
  RunFilterTokenType,
  runsFilterForSearchTokens,
  useQueryPersistedRunFilters,
  useRunsFilterInput,
} from '../../runs/RunsFilterInput';
import {HourWindow} from '../../runs/useHourWindow';
import {usePaginatedRunsTableRuns} from '../../runs/usePaginatedRunsTableRuns';
import {useRunsForTimeline} from '../../runs/useRunsForTimeline';
import {StickyTableContainer} from '../../ui/StickyTableContainer';

const BACKFILL_RUNS_HOUR_WINDOW_KEY = 'dagster.backfill-run-timeline-hour-window';
const PAGE_SIZE = 25;

const filters: RunFilterTokenType[] = [
  'tag',
  'snapshotId',
  'id',
  'job',
  'pipeline',
  'partition',
  'status',
];

export const BackfillRunsTab = ({
  backfill,
  view: propView,
}: {
  backfill: BackfillDetailsBackfillFragment;
  view: 'timeline' | 'list' | 'both';
}) => {
  const [_view, setView] = useQueryPersistedState<'timeline' | 'list'>({
    defaults: {view: 'timeline'},
    queryKey: 'view',
  });
  const view = propView === 'both' ? _view : propView;

  const [filterTokens, setFilterTokens] = useQueryPersistedRunFilters();
  const queryStringFilters = runsFilterForSearchTokens(filterTokens);

  const {button, activeFiltersJsx} = useRunsFilterInput({
    tokens: filterTokens,
    onChange: setFilterTokens,
    enabledFilters: filters,
  });

  const {rangeMs, hourWindow, setHourWindow, onPageEarlier, onPageLater, onPageNow} =
    useTimelineRange({
      maxNowMs: backfill.endTimestamp ? backfill.endTimestamp * 1000 : undefined,
      hourWindowStorageKey: BACKFILL_RUNS_HOUR_WINDOW_KEY,
      hourWindowDefault: '1',
      lookaheadHours: 0.1, // no ticks, so miminal "future" needed
    });

  const filter: RunsFilter = useMemo(
    () => ({
      ...queryStringFilters,
      tags: [...(queryStringFilters.tags || []), {key: DagsterTag.Backfill, value: backfill.id}],
    }),
    [backfill, queryStringFilters],
  );

  const annotations = useMemo(
    () =>
      backfill.endTimestamp
        ? [
            {ms: backfill.timestamp * 1000, label: 'Start'},
            {ms: backfill.endTimestamp * 1000, label: 'End'},
          ]
        : [{ms: backfill.timestamp * 1000, label: 'Start'}],
    [backfill.timestamp, backfill.endTimestamp],
  );

  const actionBarComponents = (
    <Box flex={{direction: 'column'}}>
      <Box
        flex={{direction: 'row', gap: 16}}
        style={{position: 'sticky', top: 0, left: 0, right: 0}}
      >
        {view === 'list' && button}
        {propView === 'both' ? (
          <ButtonGroup
            activeItems={new Set([view])}
            onClick={(id: 'timeline' | 'list') => {
              setView(id);
            }}
            buttons={[
              {id: 'timeline', icon: 'gantt_waterfall', label: 'Timeline'},
              {id: 'list', icon: 'list', label: 'List'},
            ]}
          />
        ) : undefined}
        <div style={{flex: 1}} />
        {view === 'timeline' && (
          <ButtonGroup<HourWindow>
            activeItems={new Set([hourWindow])}
            buttons={[
              {id: '1', label: '1hr'},
              {id: '6', label: '6hr'},
              {id: '12', label: '12hr'},
              {id: '24', label: '24hr'},
            ]}
            onClick={(hrWindow: HourWindow) => setHourWindow(hrWindow)}
          />
        )}
        {view === 'timeline' && (
          <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
            <Button onClick={onPageEarlier}>&larr;</Button>
            <Button onClick={onPageNow}>{backfill.endTimestamp ? 'Jump to end' : 'Now'}</Button>
            <Button onClick={onPageLater}>&rarr;</Button>
          </Box>
        )}
      </Box>
    </Box>
  );

  const belowActionBarComponents = activeFiltersJsx.length ? activeFiltersJsx : null;

  return view === 'timeline' ? (
    <ExecutionRunTimeline
      filter={filter}
      rangeMs={rangeMs}
      annotations={annotations}
      actionBarComponents={actionBarComponents}
    />
  ) : (
    <ExecutionRunTable
      filter={filter}
      actionBarComponents={actionBarComponents}
      belowActionBarComponents={belowActionBarComponents}
    />
  );
};

const ExecutionRunTable = ({
  filter,
  actionBarComponents,
  belowActionBarComponents,
}: {
  filter: RunsFilter;
  actionBarComponents: React.ReactNode;
  belowActionBarComponents: React.ReactNode;
}) => {
  const {queryResult, paginationProps} = usePaginatedRunsTableRuns(filter, PAGE_SIZE);
  const pipelineRunsOrError =
    queryResult.data?.pipelineRunsOrError || queryResult.previousData?.pipelineRunsOrError;

  const refreshState = useQueryRefreshAtInterval(queryResult, 15000);

  if (!pipelineRunsOrError) {
    return (
      <Box padding={{vertical: 48}}>
        <Spinner purpose="page" />
      </Box>
    );
  }
  if (pipelineRunsOrError.__typename !== 'Runs') {
    return (
      <Box padding={{vertical: 64}}>
        <NonIdealState icon="error" title="Query error" description={pipelineRunsOrError.message} />
      </Box>
    );
  }

  return (
    <>
      <div style={{position: 'absolute', right: 16, top: -32}}>
        <QueryRefreshCountdown refreshState={refreshState} />
      </div>
      <Box style={{flex: 1, overflowY: 'auto'}}>
        <StickyTableContainer $top={56}>
          <RunTable
            runs={pipelineRunsOrError.results}
            emptyState={() => (
              <Box
                padding={{vertical: 24}}
                border="top-and-bottom"
                flex={{direction: 'column', alignItems: 'center'}}
              >
                No runs have been launched.
              </Box>
            )}
            actionBarComponents={actionBarComponents}
            belowActionBarComponents={belowActionBarComponents}
            loading={queryResult.loading}
            actionBarSticky
          />
          {pipelineRunsOrError.results.length > 0 ? (
            <Box margin={{vertical: 16}}>
              <CursorHistoryControls {...paginationProps} />
            </Box>
          ) : null}
        </StickyTableContainer>
      </Box>
    </>
  );
};

const ExecutionRunTimeline = ({
  rangeMs,
  annotations,
  filter,
  actionBarComponents,
}: {
  rangeMs: [number, number];
  annotations: {label: string; ms: number}[];
  filter: RunsFilter; // note: must be memoized
  actionBarComponents: React.ReactNode;
}) => {
  const runsForTimelineRet = useRunsForTimeline({
    refreshInterval: 2 * FIFTEEN_SECONDS,
    showTicks: false,
    rangeMs,
    filter,
  });

  // Use deferred value to allow paginating quickly with the UI feeling more responsive.
  const {jobs, loading} = useDeferredValue(runsForTimelineRet);

  // Unwrap the timeline to show runs on separate rows, and sort them explicitly by
  // newest => oldest so that they match what you see in the "List" tab.
  const row = jobs[0];
  const {runs, now} = React.useMemo(() => {
    const now = Date.now();
    return row
      ? {runs: [...row.runs].sort((a, b) => b.startTime - a.startTime), now}
      : {runs: [], now};
  }, [row]);

  return (
    <>
      <div style={{position: 'absolute', right: 16, top: -32}}>
        <QueryRefreshCountdown refreshState={runsForTimelineRet.refreshState} />
      </div>
      <Box
        padding={{horizontal: 24, vertical: 12}}
        style={{position: 'sticky', top: 0, zIndex: 2, background: Colors.backgroundDefault()}}
        border="bottom"
      >
        {actionBarComponents}
      </Box>
      <ErrorBoundary region="timeline">
        <ExecutionTimeline
          loading={loading}
          rangeMs={rangeMs}
          annotations={annotations}
          runs={runs}
          now={now}
        />
      </ErrorBoundary>
    </>
  );
};
