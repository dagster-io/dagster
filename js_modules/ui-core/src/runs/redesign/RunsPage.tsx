import {Box, CursorHistoryControls, Heading, PageHeader} from '@dagster-io/ui-components';
import {useEffect, useMemo, useRef} from 'react';

import {RunsDateRangeSelect} from './RunsDateRangeSelect';
import {RunsFeed} from './RunsFeed';
import {RunsSearchInput} from './RunsSearchInput';
import {TerminateAllRuns} from './TerminateAllRuns';
import styles from './css/RunsPage.module.css';
import {useRunsFeed} from './useRunsFeed';
import {QueryRefreshCountdown} from '../../app/QueryRefresh';
import {useTrackPageView} from '../../app/analytics';
import {useIsMobile} from '../../app/layout/IsMobileContext';
import {RunsFeedView} from '../../graphql/types';
import {useDocumentTitle} from '../../hooks/useDocumentTitle';
import {RunsQueryRefetchContext} from '../RunUtils';
import {getRunsFeedDocumentTitle, getSelectedRunsFeedTab} from '../RunsFeedUtils';
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
  const selectedTab = getSelectedRunsFeedTab(filterTokens, RunsFeedView.RUNS);
  useDocumentTitle(getRunsFeedDocumentTitle(selectedTab));

  const appliedQueryKey = JSON.stringify(filter);

  const bodyRef = useRef<HTMLDivElement>(null);
  const shouldScrollToTopRef = useRef(false);

  const {entries, error, queryResult, paginationProps, refreshState} = useRunsFeed({
    filter,
    view: RunsFeedView.RUNS,
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

  return (
    <RunsQueryRefetchContext.Provider value={refetchContext}>
      <div className={styles.page}>
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
        </Box>
        <div ref={bodyRef} className={styles.body}>
          <RunsFeed
            // A new query key remounts the list, which closes any open tick dialog.
            key={appliedQueryKey}
            entries={entries}
            error={error}
            isLoading={isLoading}
            isFiltered={isFiltered}
          />
        </div>
      </div>
    </RunsQueryRefetchContext.Provider>
  );
};

// Imported via React.lazy, which requires a default export.
// eslint-disable-next-line import/no-default-export
export default RunsPage;
