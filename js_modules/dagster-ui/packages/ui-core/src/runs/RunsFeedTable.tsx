import {
  Alert,
  Body2,
  Box,
  CursorHistoryControls,
  CursorPaginationProps,
  SpinnerWithText,
  ifPlural,
} from '@dagster-io/ui-components';
import {useVirtualizer} from '@tanstack/react-virtual';
import React, {useMemo, useRef} from 'react';

import {RunBulkActionsMenu} from './RunActionsMenu';
import {RunTableEmptyState} from './RunTableEmptyState';
import {RunsQueryRefetchContext} from './RunUtils';
import {RunsFeedError} from './RunsFeedError';
import {RunsFeedRow, RunsFeedTableHeader} from './RunsFeedRow';
import {RunFilterToken} from './RunsFilterInput';
import {
  RunsFeedTableEntryFragment,
  RunsFeedTableEntryFragment_Run,
} from './types/RunsFeedRow.types';
import {useRunsFeedEntries} from './useRunsFeedEntries';
import {FIFTEEN_SECONDS, useQueryRefreshAtInterval} from '../app/QueryRefresh';
import {RunsFilter} from '../graphql/types';
import {useSelectionReducer} from '../hooks/useSelectionReducer';
import {CheckAllBox} from '../ui/CheckAllBox';
import {IndeterminateLoadingBar} from '../ui/IndeterminateLoadingBar';
import {LoadingSpinner} from '../ui/Loading';
import {Container, Inner, Row} from '../ui/VirtualizedTable';
import {numberFormatter} from '../ui/formatters';

interface RunsFeedTableProps {
  entries: RunsFeedTableEntryFragment[];
  loading: boolean;
  onAddTag?: (token: RunFilterToken) => void;
  hideTags?: string[];
  refetch: () => void;
  actionBarComponents?: React.ReactNode;
  belowActionBarComponents?: React.ReactNode;
  paginationProps: CursorPaginationProps;
  filter?: RunsFilter;
  emptyState?: () => React.ReactNode;
  scroll?: boolean;
}

export const RunsFeedTable = ({
  entries,
  loading,
  onAddTag,
  hideTags,
  refetch,
  actionBarComponents,
  belowActionBarComponents,
  paginationProps,
  filter,
  emptyState,
  scroll = true,
}: RunsFeedTableProps) => {
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

  const selectedEntries = entries.filter((e): e is RunsFeedTableEntryFragment_Run =>
    checkedIds.has(e.id),
  );

  const selectedRuns = selectedEntries.filter(
    (e): e is RunsFeedTableEntryFragment_Run => e.__typename === 'Run',
  );
  const backfillsExcluded = selectedEntries.length - selectedRuns.length;

  const actionBar = (
    <Box flex={{direction: 'column', gap: 8}}>
      <Box
        flex={{justifyContent: 'space-between'}}
        style={{width: '100%'}}
        padding={{left: 24, right: 12}}
      >
        {actionBarComponents ?? <span />}
        <Box flex={{gap: 12, alignItems: 'center'}} style={{marginRight: 8}}>
          <CursorHistoryControls {...paginationProps} style={{marginTop: 0}} />
          <RunBulkActionsMenu
            clearSelection={() => onToggleAll(false)}
            selected={selectedRuns}
            notice={
              backfillsExcluded ? (
                <Alert
                  intent="warning"
                  title={
                    <Box flex={{direction: 'column'}}>
                      <Body2>Bulk actions are currently only supported for runs.</Body2>
                      <Body2>
                        {numberFormatter.format(backfillsExcluded)}&nbsp;
                        {ifPlural(backfillsExcluded, 'backfill is', 'backfills are')} being excluded
                      </Body2>
                    </Box>
                  }
                />
              ) : null
            }
          />
        </Box>
      </Box>
      {belowActionBarComponents ? (
        <Box border="top" padding={{left: 24, right: 12, top: 12}}>
          {belowActionBarComponents}
        </Box>
      ) : null}
    </Box>
  );

  function content() {
    if (entries.length === 0 && !loading) {
      const anyFilter = !!Object.keys(filter || {}).length;
      if (emptyState) {
        return <>{emptyState()}</>;
      }

      return <RunTableEmptyState anyFilter={anyFilter} />;
    }
    return (
      <div style={{overflow: 'hidden'}}>
        <IndeterminateLoadingBar $loading={loading} />
        <Container ref={parentRef} style={scroll ? {overflow: 'auto'} : {overflow: 'visible'}}>
          <RunsFeedTableHeader
            checkbox={
              <CheckAllBox
                checkedCount={checkedIds.size}
                totalCount={entries.length}
                onToggleAll={onToggleAll}
              />
            }
          />
          {entries.length === 0 && loading && (
            <Box flex={{direction: 'row', justifyContent: 'center'}} padding={32}>
              <SpinnerWithText label="Loading runs…" />
            </Box>
          )}
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
                      refetch={refetch}
                      onAddTag={onAddTag}
                      hideTags={hideTags}
                    />
                  </div>
                </Row>
              );
            })}
          </Inner>
        </Container>
      </div>
    );
  }

  return (
    <Box
      flex={{direction: 'column', gap: 8}}
      padding={{vertical: 12}}
      style={scroll ? {height: '100%'} : {}}
    >
      {actionBar}
      {content()}
    </Box>
  );
};

export const RunsFeedTableWithFilters = ({
  filter,
  scroll,
  ...rest
}: {
  filter: RunsFilter;
} & Pick<
  RunsFeedTableProps,
  'actionBarComponents' | 'belowActionBarComponents' | 'emptyState' | 'hideTags' | 'scroll'
>) => {
  const {entries, paginationProps, queryResult} = useRunsFeedEntries(filter, 'all', true);
  const refreshState = useQueryRefreshAtInterval(queryResult, FIFTEEN_SECONDS);

  function content() {
    if (queryResult.error) {
      return <RunsFeedError error={queryResult.error} />;
    }
    if (queryResult.loading && !queryResult.data) {
      return (
        <Box flex={{direction: 'column', gap: 32}} padding={{vertical: 8}} border="top">
          <LoadingSpinner purpose="page" />
        </Box>
      );
    }

    return (
      <RunsFeedTable
        entries={entries}
        loading={queryResult.loading}
        refetch={refreshState.refetch}
        paginationProps={paginationProps}
        scroll={scroll ?? false}
        {...rest}
      />
    );
  }

  return (
    <RunsQueryRefetchContext.Provider value={{refetch: refreshState.refetch}}>
      {content()}
    </RunsQueryRefetchContext.Provider>
  );
};
