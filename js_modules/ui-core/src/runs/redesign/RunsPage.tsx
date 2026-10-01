import {Box, CursorHistoryControls, Heading, PageHeader} from '@dagster-io/ui-components';
import {useEffect, useMemo, useRef} from 'react';

import {RunsFeedList} from './RunsFeedList';
import styles from './css/RunsPage.module.css';
import {MappedRunsFeedEntry} from './mapRunsFeedData';
import {useRunsFeed} from './useRunsFeed';
import {ApolloError} from '../../apollo-client';
import {PythonErrorInfo} from '../../app/PythonErrorInfo';
import {QueryRefreshCountdown} from '../../app/QueryRefresh';
import {useTrackPageView} from '../../app/analytics';
import {PythonErrorFragment} from '../../app/types/PythonErrorFragment.types';
import {RunsFeedView, RunsFilter} from '../../graphql/types';
import {useDocumentTitle} from '../../hooks/useDocumentTitle';
import {RunTableEmptyState} from '../RunTableEmptyState';
import {RunsQueryRefetchContext} from '../RunUtils';
import {RunsFeedError} from '../RunsFeedError';
import {
  getRunsFeedDocumentTitle,
  getRunsFeedQueryView,
  getSelectedRunsFeedTab,
  useQueryPersistedRunsFeedView,
} from '../RunsFeedUtils';
import {runsFilterForSearchTokens, useQueryPersistedRunFilters} from '../RunsFilterUtils';

export const RunsPage = () => {
  useTrackPageView();

  const [filterTokens] = useQueryPersistedRunFilters();
  const filter = runsFilterForSearchTokens(filterTokens);
  const [view] = useQueryPersistedRunsFeedView();
  const selectedTab = getSelectedRunsFeedTab(filterTokens, view);
  useDocumentTitle(getRunsFeedDocumentTitle(selectedTab));

  const queryView = getRunsFeedQueryView(selectedTab, view);
  const appliedQueryKey = JSON.stringify({filter, view: queryView});

  // A new query remounts with an empty cursor stack; Back/Forward within one query keeps it.
  return <RunsPageContent key={appliedQueryKey} filter={filter} view={queryView} />;
};

type RunsPageContentProps = {
  filter: RunsFilter;
  view: RunsFeedView;
};

const RunsPageContent = ({filter, view}: RunsPageContentProps) => {
  const bodyRef = useRef<HTMLDivElement>(null);
  const shouldScrollToTopRef = useRef(false);

  const {entries, error, queryResult, paginationProps, refreshState} = useRunsFeed({
    filter,
    view,
    skip: false,
  });

  const isLoading = queryResult.loading;
  const isFiltered = Object.keys(filter).length > 0;
  const {cursor} = paginationProps;

  // Scroll after the new page renders. A cached page never sets loading, so the cursor is a dependency.
  useEffect(() => {
    if (shouldScrollToTopRef.current && !isLoading) {
      shouldScrollToTopRef.current = false;
      if (bodyRef.current) {
        bodyRef.current.scrollTop = 0;
      }
    }
  }, [cursor, isLoading]);

  const refetchContext = useMemo(() => ({refetch: refreshState.refetch}), [refreshState.refetch]);

  const popCursor = () => {
    shouldScrollToTopRef.current = true;
    paginationProps.popCursor();
  };

  const advanceCursor = () => {
    shouldScrollToTopRef.current = true;
    paginationProps.advanceCursor();
  };

  return (
    <div className={styles.page}>
      <PageHeader
        title={
          <Heading size={16} weight={600}>
            Runs
          </Heading>
        }
        right={<QueryRefreshCountdown refreshState={refreshState} />}
      />
      <Box
        flex={{alignItems: 'center', justifyContent: 'flex-end'}}
        padding={{vertical: 12, horizontal: 24}}
        border="bottom"
      >
        <CursorHistoryControls
          {...paginationProps}
          popCursor={popCursor}
          advanceCursor={advanceCursor}
          style={{marginTop: 0}}
        />
      </Box>
      <div ref={bodyRef} className={styles.body}>
        <RunsQueryRefetchContext.Provider value={refetchContext}>
          <RunsFeed entries={entries} error={error} isLoading={isLoading} isFiltered={isFiltered} />
        </RunsQueryRefetchContext.Provider>
      </div>
    </div>
  );
};

type RunsFeedProps = {
  entries: MappedRunsFeedEntry[];
  error: ApolloError | PythonErrorFragment | undefined;
  isLoading: boolean;
  isFiltered: boolean;
};

const RunsFeed = ({entries, error, isLoading, isFiltered}: RunsFeedProps) => {
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
    return <RunTableEmptyState anyFilter={isFiltered} />;
  }

  return <RunsFeedList entries={entries} isLoading={isLoading} />;
};

// Imported via React.lazy, which requires a default export.
// eslint-disable-next-line import/no-default-export
export default RunsPage;
