import {
  Box,
  Button,
  CursorHistoryControls,
  Heading,
  Icon,
  PageHeader,
  Tooltip,
} from '@dagster-io/ui-components';
import {useEffect, useMemo, useRef, useState} from 'react';

import {BulkRunActionsBar} from './BulkRunActionsBar';
import {RunsDateRangeSelect} from './RunsDateRangeSelect';
import {RunsFeed} from './RunsFeed';
import {RunsSearchInput} from './RunsSearchInput';
import {TerminateAllRuns} from './TerminateAllRuns';
import styles from './css/RunsPage.module.css';
import {MappedRun, MappedRunsFeedEntry} from './mapRunsFeedData';
import {useRunsFeed} from './useRunsFeed';
import {QueryRefreshCountdown} from '../../app/QueryRefresh';
import {useTrackPageView} from '../../app/analytics';
import {useIsMobile} from '../../app/layout/IsMobileContext';
import {RunsFeedView} from '../../graphql/types';
import {useDocumentTitle} from '../../hooks/useDocumentTitle';
import {SelectionToggle, useSelectionReducer} from '../../hooks/useSelectionReducer';
import {RunsQueryRefetchContext} from '../RunUtils';
import {getRunsFeedDocumentTitle, getSelectedRunsFeedTab} from '../RunsFeedUtils';
import {
  RunFilterToken,
  runsFilterForSearchTokens,
  useQueryPersistedRunFilters,
} from '../RunsFilterUtils';

const isCreatedDateToken = ({token}: RunFilterToken) =>
  token === 'created_date_after' || token === 'created_date_before';

const isRun = (entry: MappedRunsFeedEntry): entry is MappedRun => entry.__typename === 'Run';

export const RunsPage = () => {
  useTrackPageView();
  const isMobile = useIsMobile();
  const canSelectRuns = !isMobile;

  const [filterTokens, setFilterTokens] = useQueryPersistedRunFilters({behavior: 'push'});
  const filter = runsFilterForSearchTokens(filterTokens);
  const dateTokens = filterTokens.filter(isCreatedDateToken);
  const searchTokens = filterTokens.filter((token) => !isCreatedDateToken(token));
  const selectedTab = getSelectedRunsFeedTab(filterTokens, RunsFeedView.RUNS);
  useDocumentTitle(getRunsFeedDocumentTitle(selectedTab));

  const appliedQueryKey = JSON.stringify(filter);

  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const shouldScrollToTopRef = useRef(false);

  const {entries, error, queryResult, paginationProps, refreshState} = useRunsFeed({
    filter,
    view: RunsFeedView.RUNS,
    skip: false,
  });

  const isLoading = queryResult.loading;
  const isFiltered = Object.keys(filter).length > 0;
  const {cursor} = paginationProps;

  // Narrows the type only: the page queries the runs view, so every entry is a run.
  const runs = useMemo(() => entries.filter(isRun), [entries]);
  const runIds = useMemo(() => runs.map((run) => run.id), [runs]);
  const [{checkedIds}, {onToggleFactory, onToggleAll, clearSelection}] =
    useSelectionReducer(runIds);
  const [isBulkActionsBarOpen, setIsBulkActionsBarOpen] = useState(false);
  const selectedRuns = useMemo(
    () => runs.filter((run) => checkedIds.has(run.id)),
    [runs, checkedIds],
  );

  // Scroll after the new page renders. A cached page never sets loading, so the cursor is a dependency.
  useEffect(() => {
    if (shouldScrollToTopRef.current && !isLoading) {
      shouldScrollToTopRef.current = false;
      if (scrollAreaRef.current) {
        scrollAreaRef.current.scrollTop = 0;
      }
    }
  }, [cursor, isLoading]);

  useEffect(() => {
    if (scrollAreaRef.current) {
      scrollAreaRef.current.scrollTop = 0;
    }
  }, [appliedQueryKey]);

  // Pruning keeps runs that are on both the old and new page or filter, so clear explicitly.
  useEffect(() => {
    clearSelection();
  }, [appliedQueryKey, cursor, clearSelection]);

  const refetchContext = useMemo(() => ({refetch: refreshState.refetch}), [refreshState.refetch]);

  const popCursor = () => {
    shouldScrollToTopRef.current = true;
    paginationProps.popCursor();
  };

  const advanceCursor = () => {
    shouldScrollToTopRef.current = true;
    paginationProps.advanceCursor();
  };

  const toggleRun = (runId: string, toggle: SelectionToggle) => {
    if (toggle.checked) {
      setIsBulkActionsBarOpen(true);
    }
    onToggleFactory(runId)(toggle);
  };

  return (
    <RunsQueryRefetchContext.Provider value={refetchContext}>
      <div className={styles.container}>
        <PageHeader
          title={
            <Heading size={16} weight={600}>
              Runs
            </Heading>
          }
          right={
            <Box flex={{alignItems: 'center', gap: 12}}>
              <QueryRefreshCountdown refreshState={refreshState} />
              <CursorHistoryControls
                {...paginationProps}
                popCursor={popCursor}
                advanceCursor={advanceCursor}
                style={{marginTop: 0}}
                iconOnly={isMobile}
              />
            </Box>
          }
        />
        <Box flex={{alignItems: 'center', gap: 12}} border="bottom" className={styles.toolbar}>
          <RunsDateRangeSelect
            tokens={dateTokens}
            onChange={(tokens) => setFilterTokens([...searchTokens, ...tokens])}
          />
          <Box flex={{grow: 1}}>
            <RunsSearchInput
              tokens={searchTokens}
              onChange={(tokens) => setFilterTokens([...tokens, ...dateTokens])}
            />
          </Box>
          <TerminateAllRuns
            // Remounting on a new query closes the dialog so it can't act on a filter it wasn't
            // opened for.
            key={appliedQueryKey}
            filter={filter}
          />
          {canSelectRuns && (
            <Tooltip content="Select runs" position="bottom-end" canShow={!isBulkActionsBarOpen}>
              <Button
                intent="none"
                icon={<Icon name="checklist" />}
                aria-label="Select runs"
                disabled={isBulkActionsBarOpen}
                onClick={() => setIsBulkActionsBarOpen(true)}
              />
            </Tooltip>
          )}
        </Box>
        {isBulkActionsBarOpen && (
          <BulkRunActionsBar
            selectedRuns={selectedRuns}
            pageRunCount={runs.length}
            onToggleAll={onToggleAll}
            clearSelection={clearSelection}
            onClose={() => {
              clearSelection();
              setIsBulkActionsBarOpen(false);
            }}
          />
        )}
        <div ref={scrollAreaRef} className={styles.scrollArea}>
          <RunsFeed
            // A new query key remounts the list, which closes any open tick dialog.
            key={appliedQueryKey}
            entries={entries}
            error={error}
            isLoading={isLoading}
            isFiltered={isFiltered}
            checkedIds={canSelectRuns ? checkedIds : undefined}
            onToggleRun={canSelectRuns ? toggleRun : undefined}
          />
        </div>
      </div>
    </RunsQueryRefetchContext.Provider>
  );
};

// Imported via React.lazy, which requires a default export.
// eslint-disable-next-line import/no-default-export
export default RunsPage;
