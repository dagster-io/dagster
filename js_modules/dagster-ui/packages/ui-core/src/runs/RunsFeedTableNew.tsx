import {Box, CursorPaginationProps, SpinnerWithText} from '@dagster-io/ui-components';
import {useVirtualizer} from '@tanstack/react-virtual';
import React, {useEffect, useMemo, useRef, useState, useCallback} from 'react';
import faker from 'faker';

import {QueuedRunCriteriaDialog} from './QueuedRunCriteriaDialog';
import {RunTableEmptyState} from './RunTableEmptyState';
import {RunsQueryRefetchContext} from './RunUtils';
import {RunsFeedError} from './RunsFeedError';
import {RunsFeedRow, RunsFeedTableHeader, SkeletonRow, SelectedTagsProvider} from './RunsFeedRowNew';
import {RunFilterToken} from './RunsFilterInput';
import {
  RunsFeedTableEntryFragment,
  RunsFeedTableEntryFragment_Run,
} from './types/RunsFeedTableEntryFragment.types';
import {useRunsFeedEntries} from './useRunsFeedEntries';
import {FIFTEEN_SECONDS, useQueryRefreshAtInterval} from '../app/QueryRefresh';
import {RunsFeedView, RunsFilter, RunStatus} from '../graphql/types';
import {useSelectionReducer} from '../hooks/useSelectionReducer';
import {BackfillPartitionsRequestedDialog} from '../instance/backfill/BackfillPartitionsRequestedDialog';
import {IndeterminateLoadingBar} from '../ui/IndeterminateLoadingBar';
import {Container, Inner, Row} from '../ui/VirtualizedTable';

interface RunsFeedTableNewProps {
  entries: RunsFeedTableEntryFragment[];
  loading: boolean;
  onAddTag?: (token: RunFilterToken) => void;
  hideTags?: string[];
  refetch: () => void;
  actionBarComponents?: React.ReactNode;
  belowActionBarComponents?: React.ReactNode;
  terminateAllRunsButton?: React.ReactNode;
  paginationProps: CursorPaginationProps;
  filter?: RunsFilter;
  emptyState?: () => React.ReactNode;
  scroll?: boolean;
  statusFilter?: 'all' | 'in-progress' | 'failed' | 'queued';
}

// Potentially other modals in the future
export type RunsFeedDialogState =
  | {type: 'partitions'; backfillId: string}
  | {type: 'queue-criteria'; entry: RunsFeedTableEntryFragment};

export const RunsFeedTableNew = ({
  entries,
  loading,
  onAddTag,
  hideTags,
  refetch,
  actionBarComponents,
  belowActionBarComponents,
  terminateAllRunsButton,
  paginationProps,
  filter,
  emptyState,
  scroll = true,
  statusFilter = 'all',
}: RunsFeedTableNewProps) => {
  console.log('entries', entries);
  const parentRef = useRef<HTMLDivElement | null>(null);
  const [additionalEntries, setAdditionalEntries] = useState<RunsFeedTableEntryFragment[]>([]);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [skeletonEntries, setSkeletonEntries] = useState<Set<string>>(new Set());

  // Helper functions from defaultMocks
  const hyphenatedName = (wordCount = 2) =>
    faker.random.words(wordCount).replace(/ /g, '-').toLowerCase();
  const randomId = () => faker.datatype.uuid();

  // Function to generate mock entries using faker (matching defaultMocks.ts)
  const generateMockEntries = useCallback((count: number): RunsFeedTableEntryFragment[] => {
    const mockEntries: RunsFeedTableEntryFragment[] = [];
    
    for (let i = 0; i < count; i++) {
      const status = faker.random.arrayElement([
        RunStatus.SUCCESS,
        RunStatus.SUCCESS, // Weight SUCCESS more heavily
        RunStatus.STARTED,
        RunStatus.FAILURE,
        RunStatus.QUEUED,
        RunStatus.STARTING,
        RunStatus.NOT_STARTED,
        RunStatus.CANCELING,
        RunStatus.CANCELED,
      ]);
      
      const now = Date.now() / 1000;
      const creationTime = now - faker.datatype.number({min: 10, max: 7200}); // 10 seconds to 2 hours ago
      
      let startTime = null;
      let endTime = null;
      
      // Set times based on status to ensure logical consistency
      if (status === RunStatus.SUCCESS || status === RunStatus.FAILURE) {
        // Completed runs should have both start and end times
        const runDuration = faker.datatype.number({min: 15, max: 900}); // 15 seconds to 15 minutes
        endTime = now - faker.datatype.number({min: 5, max: 180}); // ended 5s to 3min ago
        startTime = endTime - runDuration;
      } else if (status === RunStatus.STARTED) {
        // Started runs have start time but no end time
        startTime = now - faker.datatype.number({min: 10, max: 600}); // started 10s to 10min ago
      } else if (status === RunStatus.STARTING || status === RunStatus.CANCELING) {
        // These might have start times
        startTime = faker.datatype.boolean() 
          ? now - faker.datatype.number({min: 2, max: 30}) // started 2s to 30s ago
          : null;
      }
      
      // Generate realistic tags
      const baseTags = [...new Array(faker.datatype.number({min: 5, max: 12}))].map(() => ({
        key: faker.random.arrayElement([
          'dagster/agent_id',
          'dagster/git_commit_hash',
          'dagster/image',
          'dagster/from_ui',
          'environment',
          'team',
          'partition_date',
          'retry_count',
          'priority',
          'source_system',
        ]),
        value: faker.random.arrayElement([
          faker.datatype.uuid().slice(0, 8),
          faker.git.commitSha().slice(0, 12),
          faker.datatype.boolean().toString(),
          faker.random.arrayElement(['production', 'staging', 'development']),
          faker.random.arrayElement(['data-engineering', 'analytics', 'ml-ops']),
          faker.date.recent().toISOString().slice(0, 10),
          faker.datatype.number({min: 0, max: 3}).toString(),
          faker.random.arrayElement(['high', 'medium', 'low']),
        ]),
      }));

      // Add launch type tags for realistic distribution  
      const launchTags = [];
      if (faker.datatype.number({min: 1, max: 10}) <= 8) {
        const launchType = faker.random.arrayElement([
          'user',
          'schedule', 
          'sensor',
          'automation',
          'backfill',
        ]);

        switch (launchType) {
          case 'user':
            launchTags.push({key: 'user', value: faker.internet.email()});
            break;
          case 'schedule':
            launchTags.push({key: 'dagster/schedule_name', value: `${hyphenatedName()}_schedule`});
            break;
          case 'sensor':
            launchTags.push({key: 'dagster/sensor_name', value: `${hyphenatedName()}_sensor`});
            break;
          case 'automation':
            launchTags.push(
              {key: 'dagster/auto_materialize', value: 'true'},
              {key: 'dagster/from_automation_condition', value: 'true'},
              {key: 'dagster/sensor_name', value: 'default_automation_condition_sensor'},
            );
            break;
          case 'backfill':
            launchTags.push(
              {key: 'dagster/backfill', value: faker.datatype.uuid().slice(0, 8)},
              {key: 'user', value: faker.internet.email()},
            );
            break;
        }
      }
      
      mockEntries.push({
        __typename: 'Run',
        id: randomId(),
        jobName: hyphenatedName(),
        runStatus: status,
        creationTime,
        startTime,
        endTime,
        tags: [...baseTags, ...launchTags],
        assetSelection: [...new Array(faker.datatype.number({min: 0, max: 8}))].map(() => ({
          path: faker.random.words(faker.datatype.number({min: 1, max: 3})).split(' '),
        })),
        assetCheckSelection: [...new Array(faker.datatype.number({min: 0, max: 5}))].map(() => ({
          name: hyphenatedName(),
          assetKey: {
            path: faker.random.words(faker.datatype.number({min: 1, max: 3})).split(' '),
          },
        })),
      } as RunsFeedTableEntryFragment);
    }
    
    return mockEntries;
  }, []);

  // Combine original and additional entries
  const allEntries = useMemo(() => [...entries, ...additionalEntries], [entries, additionalEntries]);

  // Filter and sort entries by creation time (newest first)
  const sortedEntries = useMemo(() => {
    if (allEntries.length === 0) {
      return allEntries;
    }

    // First filter by status
    let filtered = allEntries;
    if (statusFilter !== 'all') {
      filtered = allEntries.filter((entry) => {
        const status = entry.runStatus;
        switch (statusFilter) {
          case 'in-progress':
            return [
              RunStatus.NOT_STARTED,
              RunStatus.STARTING,
              RunStatus.STARTED,
              RunStatus.CANCELING,
            ].includes(status);
          case 'queued':
            return status === RunStatus.QUEUED;
          case 'failed':
            return status === RunStatus.FAILURE;
          default:
            return true;
        }
      });
    }

    // Then sort by creation time
    const sorted = [...filtered].sort((a, b) => {
      // Handle potential undefined/null values
      const timeA = a.creationTime ?? 0;
      const timeB = b.creationTime ?? 0;
      return timeB - timeA; // Newest first (descending order)
    });

    console.log(`Filtered by ${statusFilter} status - showing ${sorted.length} entries`);
    sorted.slice(0, 3).forEach((entry, i) => {
      console.log(`${i + 1}. Status: ${entry.runStatus}, Created: ${new Date(entry.creationTime * 1000).toLocaleString()}`);
    });

    return sorted;
  }, [allEntries, statusFilter]);

  const entryIds = useMemo(() => sortedEntries.map((e) => e.id), [sortedEntries]);
  const [{checkedIds}, {onToggleFactory, onToggleAll}] = useSelectionReducer(entryIds);
  const [dialog, setDialog] = useState<null | RunsFeedDialogState>(null);

  const rowVirtualizer = useVirtualizer({
    count: sortedEntries.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 56, // Updated height for our new row design
    overscan: 15,
  });

  const totalHeight = rowVirtualizer.getTotalSize();
  const items = rowVirtualizer.getVirtualItems();

  // Function to load more entries
  const loadMoreEntries = useCallback(async () => {
    if (isLoadingMore) return;
    
    setIsLoadingMore(true);
    
    // Generate the new entries immediately but mark them as skeleton
    const newEntries = generateMockEntries(100);
    const skeletonIds = new Set(newEntries.map(entry => entry.id));
    
    // Add skeleton entries immediately
    setAdditionalEntries(prev => [...prev, ...newEntries]);
    setSkeletonEntries(prev => new Set([...prev, ...skeletonIds]));
    
    // After 1 second, remove skeleton state and show real content
    setTimeout(() => {
      setSkeletonEntries(prev => {
        const newSet = new Set(prev);
        skeletonIds.forEach(id => newSet.delete(id));
        return newSet;
      });
      setIsLoadingMore(false);
    }, 1000);
  }, [isLoadingMore, generateMockEntries]);

  // Scroll detection for infinite loading
  useEffect(() => {
    const scrollElement = parentRef.current;
    if (!scrollElement) return;

    const handleScroll = () => {
      const { scrollTop, scrollHeight, clientHeight } = scrollElement;
      // Trigger when user is within 200px of bottom
      if (scrollHeight - scrollTop <= clientHeight + 200 && !isLoadingMore) {
        loadMoreEntries();
      }
    };

    scrollElement.addEventListener('scroll', handleScroll);
    return () => scrollElement.removeEventListener('scroll', handleScroll);
  }, [loadMoreEntries, isLoadingMore]);

  const selectedEntries = sortedEntries.filter((e): e is RunsFeedTableEntryFragment_Run =>
    checkedIds.has(e.id),
  );

  const selectedRuns = selectedEntries.filter(
    (e): e is RunsFeedTableEntryFragment_Run => e.__typename === 'Run',
  );
  const backfillsExcluded = selectedEntries.length - selectedRuns.length;

  const resetScrollOnLoad = useRef(false);
  useEffect(() => {
    // When you click "Next page" from the bottom of page 1, we show the indeterminate
    // loading state and want to scroll to the top when the new results arrive. It looks
    // bad to do it immediately, and the `entries` can also change on their own (and
    // sometimes with new rows), so we do this explicitly for pagination cases using a ref.
    if (!loading && resetScrollOnLoad.current) {
      resetScrollOnLoad.current = false;
      if (parentRef.current) {
        parentRef.current.scrollTop = 0;
      }
    }
  }, [loading]);

  const actionBar = (
    <Box flex={{direction: 'column', gap: 8}}>
      <Box
        flex={{justifyContent: 'space-between'}}
        style={{width: '100%', borderBottom: '1px solid #e1e5e9'}}
        padding={{left: 16, right: 16, bottom: 16}}
      >
        {actionBarComponents ?? <span />}
        <Box flex={{gap: 12, alignItems: 'center'}} style={{marginRight: 8}}>
          {/* Pagination and bulk actions removed */}
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
    const header = <RunsFeedTableHeader />;

    if (sortedEntries.length === 0 && !loading) {
      const anyFilter = !!Object.keys(filter || {}).length;
      if (emptyState) {
        return (
          <div style={{overflow: 'hidden'}}>
            <IndeterminateLoadingBar $loading={loading} />
            {header}
            <div style={{minHeight: 82}}>{emptyState()}</div>
          </div>
        );
      }

      return (
        <div style={{overflow: 'hidden'}}>
          {header}
          <RunTableEmptyState anyFilter={anyFilter} />
        </div>
      );
    }

    return (
      <div
        style={
          scroll
            ? {overflow: 'hidden', display: 'flex', flexDirection: 'column'}
            : {overflow: 'hidden'}
        }
      >
        <BackfillPartitionsRequestedDialog
          backfillId={dialog?.type === 'partitions' ? dialog.backfillId : undefined}
          onClose={() => setDialog(null)}
        />
        <QueuedRunCriteriaDialog
          run={dialog?.type === 'queue-criteria' ? dialog.entry : undefined}
          isOpen={dialog?.type === 'queue-criteria'}
          onClose={() => setDialog(null)}
        />

        <IndeterminateLoadingBar $loading={loading} />
        <Container ref={parentRef} style={scroll ? {overflow: 'auto'} : {overflow: 'visible'}}>
          {header}
          {sortedEntries.length === 0 && loading && (
            <Box flex={{direction: 'row', justifyContent: 'center'}} padding={32} style={{margin: 'auto'}}>
              <SpinnerWithText label="Loading runs…" />
            </Box>
          )}
          <Inner $totalHeight={totalHeight}>
            {items.map(({index, size, start, key}) => {
              const entry = sortedEntries[index];
              if (!entry) {
                return <span key={key} />;
              }
              const isSkeleton = skeletonEntries.has(entry.id);
              return (
                <Row $height={size} $start={start} data-key={key} key={key}>
                  <div ref={rowVirtualizer.measureElement} data-index={index}>
                    {isSkeleton ? <SkeletonRow key={key} /> : <RunsFeedRow key={key} entry={entry} />}
                  </div>
                </Row>
              );
            })}
          </Inner>
          {isLoadingMore && (
            <Box flex={{direction: 'row', justifyContent: 'center'}} padding={16}>
              <SpinnerWithText label="Loading more runs…" />
            </Box>
          )}
        </Container>
      </div>
    );
  }

  return (
    <SelectedTagsProvider>
      <Box
        flex={{direction: 'column', gap: 8}}
        padding={{vertical: 12}}
        style={scroll ? {height: '100%', minHeight: 0} : {}}
      >
        {actionBar}
        {content()}
      </Box>
    </SelectedTagsProvider>
  );
};

export const RunsFeedTableNewWithFilters = ({
  filter,
  scroll,
  includeRunsFromBackfills,
  ...rest
}: {
  filter: RunsFilter;
  includeRunsFromBackfills: boolean;
} & Pick<
  RunsFeedTableNewProps,
  'actionBarComponents' | 'belowActionBarComponents' | 'emptyState' | 'hideTags' | 'scroll'
>) => {
  const {entries, paginationProps, queryResult} = useRunsFeedEntries({
    view: includeRunsFromBackfills ? RunsFeedView.RUNS : RunsFeedView.ROOTS,
    skip: false,
    filter,
  });
  const refreshState = useQueryRefreshAtInterval(queryResult, FIFTEEN_SECONDS);

  function content() {
    if (queryResult.error) {
      return <RunsFeedError error={queryResult.error} />;
    }

    return (
      <RunsFeedTableNew
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
