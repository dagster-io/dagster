import {CursorHistoryControls} from '@dagster-io/ui-components';
import {ReactNode, useMemo} from 'react';

import {RunsFeed} from './RunsFeed';
import styles from './css/MobileRunsFeedWithFilters.module.css';
import {useRunsFeed} from './useRunsFeed';
import {RunsFeedView, RunsFilter} from '../../graphql/types';
import {RunsQueryRefetchContext} from '../RunUtils';

type Props = {
  filter: RunsFilter;
  includeRunsFromBackfills: boolean;
  actionBarComponents?: ReactNode;
  belowActionBarComponents?: ReactNode;
  emptyState?: () => ReactNode;
};

/**
 * `RunsFeedTableWithFilters` in the mobile layout: the runs page's card list instead of the
 * wide table. Bulk actions and tag display are desktop-only.
 */
export const MobileRunsFeedWithFilters = ({
  filter,
  includeRunsFromBackfills,
  actionBarComponents,
  belowActionBarComponents,
  emptyState,
}: Props) => {
  const {entries, error, queryResult, paginationProps, refreshState} = useRunsFeed({
    filter,
    view: includeRunsFromBackfills ? RunsFeedView.RUNS : RunsFeedView.ROOTS,
    skip: false,
  });
  const refetchContext = useMemo(() => ({refetch: refreshState.refetch}), [refreshState.refetch]);

  return (
    <RunsQueryRefetchContext.Provider value={refetchContext}>
      <div className={styles.actionBar}>
        {actionBarComponents ?? <span />}
        <CursorHistoryControls {...paginationProps} style={{marginTop: 0}} iconOnly />
      </div>
      {belowActionBarComponents ? (
        <div className={styles.belowActionBar}>{belowActionBarComponents}</div>
      ) : null}
      <RunsFeed
        entries={entries}
        error={error}
        isLoading={queryResult.loading}
        isFiltered={Object.keys(filter).length > 0}
        emptyState={emptyState}
      />
    </RunsQueryRefetchContext.Provider>
  );
};

// Imported via `lazy`, which requires a default export.
// eslint-disable-next-line import/no-default-export
export default MobileRunsFeedWithFilters;
