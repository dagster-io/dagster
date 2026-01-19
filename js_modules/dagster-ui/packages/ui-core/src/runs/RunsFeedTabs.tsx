import {Tabs, TokenizingFieldValue} from '@dagster-io/ui-components';
import isEqual from 'lodash/isEqual';
import {useMemo} from 'react';
import {useLocation} from 'react-router-dom';

import {failedStatuses, inProgressStatuses, queuedStatuses} from './RunStatuses';
import {runsPathWithFilters, useQueryPersistedRunFilters} from './RunsFilterInput';
import {gql, useQuery} from '../apollo-client';
import {RunFeedTabsCountQuery, RunFeedTabsCountQueryVariables} from './types/RunsFeedTabs.types';
import {RunStatus, RunsFeedView, RunsFilter} from '../graphql/types';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {TabLink} from '../ui/TabLink';

type SelectedTab = ReturnType<typeof useSelectedRunsFeedTab>;

const getDocumentTitle = (selected: SelectedTab) => {
  switch (selected) {
    case 'all':
      return '运行记录 | 全部';
    case 'backfills':
      return '运行记录 | 历史补算';
    case 'failed':
      return '运行记录 | 失败';
    case 'in-progress':
      return '运行记录 | 进行中';
    case 'queued':
      return '运行记录 | 排队中';
    case 'scheduled':
      return '运行记录 | 定时';
    default:
      return '运行记录';
  }
};

export const useRunsFeedTabs = (selectedTab: SelectedTab, filter: RunsFilter = {}) => {
  const queryResult = useQuery<RunFeedTabsCountQuery, RunFeedTabsCountQueryVariables>(
    RUN_FEED_TABS_COUNT_QUERY,
    {
      variables: {
        queuedFilter: {...filter, statuses: Array.from(queuedStatuses)},
        inProgressFilter: {...filter, statuses: Array.from(inProgressStatuses)},
        view: RunsFeedView.RUNS,
      },
    },
  );

  const {data: countData} = queryResult;
  const {queuedCount, inProgressCount} = useMemo(() => {
    return {
      queuedCount:
        countData?.queuedCount?.__typename === 'RunsFeedCount' ? countData.queuedCount.count : null,
      inProgressCount:
        countData?.inProgressCount?.__typename === 'RunsFeedCount'
          ? countData.inProgressCount.count
          : null,
    };
  }, [countData]);

  const [filterTokens] = useQueryPersistedRunFilters();

  useDocumentTitle(getDocumentTitle(selectedTab));

  const urlForStatus = (statuses: RunStatus[], nextView?: RunsFeedView) => {
    const tokensMinusStatus = filterTokens.filter((token) => token.token !== 'status');
    const statusTokens = statuses.map((status) => ({token: 'status' as const, value: status}));
    return runsPathWithFilters([...statusTokens, ...tokensMinusStatus], '/runs', nextView);
  };

  const tabs = (
    <Tabs selectedTabId={selectedTab}>
      <TabLink id="all" title="全部" to={urlForStatus([])} />
      <TabLink id="backfills" title="历史补算" to={urlForStatus([], RunsFeedView.BACKFILLS)} />
      <TabLink
        id="queued"
        title={queuedCount !== null ? `排队中 (${queuedCount})` : `排队中`}
        to={urlForStatus(Array.from(queuedStatuses))}
      />
      <TabLink
        id="in-progress"
        title={inProgressCount !== null ? `进行中 (${inProgressCount})` : '进行中'}
        to={urlForStatus(Array.from(inProgressStatuses))}
      />
      <TabLink id="failed" title="失败" to={urlForStatus(Array.from(failedStatuses))} />
      <TabLink id="scheduled" title="定时" to="/runs/scheduled" />
    </Tabs>
  );

  return {tabs, queryResult};
};

export const useSelectedRunsFeedTab = (
  filterTokens: TokenizingFieldValue[],
  view: RunsFeedView,
) => {
  const {pathname} = useLocation();
  if (pathname === '/runs/scheduled') {
    return 'scheduled';
  }
  if (view === RunsFeedView.BACKFILLS) {
    return 'backfills';
  }
  const statusTokens = new Set(
    filterTokens.filter((token) => token.token === 'status').map((token) => token.value),
  );
  if (isEqual(queuedStatuses, statusTokens)) {
    return 'queued';
  }
  if (isEqual(inProgressStatuses, statusTokens)) {
    return 'in-progress';
  }
  if (isEqual(failedStatuses, statusTokens)) {
    return 'failed';
  }
  return 'all';
};

export const RUN_FEED_TABS_COUNT_QUERY = gql`
  query RunFeedTabsCountQuery(
    $queuedFilter: RunsFilter!
    $inProgressFilter: RunsFilter!
    $view: RunsFeedView!
  ) {
    queuedCount: runsFeedCountOrError(filter: $queuedFilter, view: $view) {
      ... on RunsFeedCount {
        count
      }
    }
    inProgressCount: runsFeedCountOrError(filter: $inProgressFilter, view: $view) {
      ... on RunsFeedCount {
        count
      }
    }
  }
`;
