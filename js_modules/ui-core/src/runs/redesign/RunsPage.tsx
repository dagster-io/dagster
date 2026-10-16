import {Box, CursorHistoryControls, Heading, PageHeader} from '@dagster-io/ui-components';
import {useEffect, useMemo, useRef} from 'react';

import {RunsDateRangeSelect} from './RunsDateRangeSelect';
import {RunsFeedList} from './RunsFeedList';
import {RunsSearchInput} from './RunsSearchInput';
import styles from './css/RunsPage.module.css';
import {MappedRunsFeedEntry} from './mapRunsFeedData';
import {useRunsFeed} from './useRunsFeed';
import {ApolloError} from '../../apollo-client';
import {PythonErrorInfo} from '../../app/PythonErrorInfo';
import {QueryRefreshCountdown} from '../../app/QueryRefresh';
import {useTrackPageView} from '../../app/analytics';
import {useIsMobile} from '../../app/layout/IsMobileContext';
import {PythonErrorFragment} from '../../app/types/PythonErrorFragment.types';
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
import {
  RunFilterToken,
  runsFilterForSearchTokens,
  useQueryPersistedRunFilters,
} from '../RunsFilterUtils';

const isCreatedDateToken = ({token}: RunFilterToken) =>
  token === 'created_date_after' || token === 'created_date_before';

export const RunsPage = () => {
  useTrackPageView();
  const isMobile = useIsMobile();

  const [filterTokens, setFilterTokens] = useQueryPersistedRunFilters({behavior: 'push'});
  const filter = runsFilterForSearchTokens(filterTokens);
  const dateTokens = filterTokens.filter(isCreatedDateToken);
  const searchTokens = filterTokens.filter((token) => !isCreatedDateToken(token));
  const [view] = useQueryPersistedRunsFeedView();
  const selectedTab = getSelectedRunsFeedTab(filterTokens, view);
  useDocumentTitle(getRunsFeedDocumentTitle(selectedTab));

  const queryView = getRunsFeedQueryView(selectedTab, view);
  const appliedQueryKey = JSON.stringify({filter, view: queryView});

  const bodyRef = useRef<HTMLDivElement>(null);
  const shouldScrollToTopRef = useRef(false);

  const {entries, error, queryResult, paginationProps, refreshState} = useRunsFeed({
    filter,
    view: queryView,
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

  useEffect(() => {
    if (bodyRef.current) {
      bodyRef.current.scrollTop = 0;
    }
  }, [appliedQueryKey]);

  const refetchContext = useMemo(() => ({refetch: refreshState.refetch}), [refreshState.refetch]);

  const popCursor = () => {
    shouldScrollToTopRef.current = true;
    paginationProps.popCursor();
  };

  const advanceCursor = () => {
    shouldScrollToTopRef.current = true;
    paginationProps.advanceCursor();
  };

  // On a phone, pagination moves into the header so the search input gets the full width.
  const paginationControls = (
    <CursorHistoryControls
      {...paginationProps}
      popCursor={popCursor}
      advanceCursor={advanceCursor}
      style={{marginTop: 0}}
      iconOnly={isMobile}
    />
  );

  return (
    <div className={styles.page}>
      <PageHeader
        title={
          <Heading size={16} weight={600}>
            Runs
          </Heading>
        }
        right={
          isMobile ? (
            <Box flex={{alignItems: 'center', gap: 12}}>
              <QueryRefreshCountdown refreshState={refreshState} />
              {paginationControls}
            </Box>
          ) : (
            <QueryRefreshCountdown refreshState={refreshState} />
          )
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
        {isMobile ? null : paginationControls}
      </Box>
      <div ref={bodyRef} className={styles.body}>
        <RunsQueryRefetchContext.Provider value={refetchContext}>
          <RunsFeed
            // A new query key remounts the list, which closes any open tick dialog.
            key={appliedQueryKey}
            entries={entries}
            error={error}
            isLoading={isLoading}
            isFiltered={isFiltered}
          />
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
        <RunTableEmptyState anyFilter={isFiltered} shrinkable={isMobile} />
      </div>
    );
  }

  return <RunsFeedList entries={entries} isLoading={isLoading} />;
};

// Imported via React.lazy, which requires a default export.
// eslint-disable-next-line import/no-default-export
export default RunsPage;
