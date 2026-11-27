import {Box} from '@dagster-io/ui-components';
import {ReactNode} from 'react';

import {RunsFeedList} from './RunsFeedList';
import styles from './css/RunsFeed.module.css';
import {MappedRunsFeedEntry} from './mapRunsFeedData';
import {ApolloError} from '../../apollo-client';
import {PythonErrorInfo} from '../../app/PythonErrorInfo';
import {useIsMobile} from '../../app/layout/IsMobileContext';
import {PythonErrorFragment} from '../../app/types/PythonErrorFragment.types';
import {SelectionToggle} from '../../hooks/useSelectionReducer';
import {RunTableEmptyState} from '../RunTableEmptyState';
import {RunsFeedError} from '../RunsFeedError';

type RunsFeedProps = {
  entries: MappedRunsFeedEntry[];
  error: ApolloError | PythonErrorFragment | undefined;
  isLoading: boolean;
  isFiltered: boolean;
  emptyState?: () => ReactNode;
  checkedIds?: Set<string>;
  /** Shows selection checkboxes when set. */
  onToggleRun?: (runId: string, toggle: SelectionToggle) => void;
};

/** The runs feed list with its error and empty states. */
export const RunsFeed = ({
  entries,
  error,
  isLoading,
  isFiltered,
  emptyState,
  checkedIds,
  onToggleRun,
}: RunsFeedProps) => {
  const isMobile = useIsMobile();

  if (error instanceof ApolloError) {
    return <RunsFeedError error={error} />;
  }

  if (error) {
    return (
      <Box padding={24}>
        <PythonErrorInfo error={error} />
      </Box>
    );
  }

  if (entries.length === 0 && !isLoading) {
    return (
      <div className={styles.emptyState}>
        {emptyState ? (
          emptyState()
        ) : (
          <RunTableEmptyState anyFilter={isFiltered} shrinkable={isMobile} />
        )}
      </div>
    );
  }

  return (
    <RunsFeedList
      entries={entries}
      isLoading={isLoading}
      checkedIds={checkedIds}
      onToggleRun={onToggleRun}
    />
  );
};
