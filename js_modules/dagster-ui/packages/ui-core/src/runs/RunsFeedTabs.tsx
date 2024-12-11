import {Colors, Tabs, TokenizingFieldValue} from '@dagster-io/ui-components';
import isEqual from 'lodash/isEqual';
import {useMemo} from 'react';
import {useLocation} from 'react-router-dom';
import styled, {css} from 'styled-components';

import {failedStatuses, inProgressStatuses, queuedStatuses} from './RunStatuses';
import {runsPathWithFilters, useQueryPersistedRunFilters} from './RunsFilterInput';
import {gql, useQuery} from '../apollo-client';
import {RunFeedTabsCountQuery, RunFeedTabsCountQueryVariables} from './types/RunsFeedTabs.types';
import {RunStatus, RunsFeedView, RunsFilter} from '../graphql/types';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {AnchorButton} from '../ui/AnchorButton';
import {TabLink} from '../ui/TabLink';

const getDocumentTitle = (selected: ReturnType<typeof useSelectedRunsFeedTab>) => {
  switch (selected) {
    case 'all':
      return 'Runs | All';
    case 'backfills':
      return 'Runs | All Backfills';
    case 'failed':
      return 'Runs | Failed';
    case 'in-progress':
      return 'Runs | In progress';
    case 'queued':
      return 'Runs | Queued';
    case 'scheduled':
      return 'Runs | Scheduled';
    default:
      return 'Runs';
  }
};

export const useRunsFeedTabs = (filter: RunsFilter = {}, view: RunsFeedView) => {
  const queryResult = useQuery<RunFeedTabsCountQuery, RunFeedTabsCountQueryVariables>(
    RUN_FEED_TABS_COUNT_QUERY,
    {
      variables: {
        queuedFilter: {...filter, statuses: Array.from(queuedStatuses)},
        inProgressFilter: {...filter, statuses: Array.from(inProgressStatuses)},
        view,
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
  const selectedTab = useSelectedRunsFeedTab(filterTokens, view);

  useDocumentTitle(getDocumentTitle(selectedTab));

  const urlForStatus = (statuses: RunStatus[], nextView?: RunsFeedView) => {
    nextView ||= view === RunsFeedView.RUNS ? RunsFeedView.RUNS : RunsFeedView.ROOTS;
    const tokensMinusStatus = filterTokens.filter((token) => token.token !== 'status');
    const statusTokens = statuses.map((status) => ({token: 'status' as const, value: status}));
    return runsPathWithFilters([...statusTokens, ...tokensMinusStatus], '/runs', nextView);
  };

  const tabs = (
    <Tabs selectedTabId={selectedTab}>
      <TabLink id="all" title="All" to={urlForStatus([])} />
      <TabLink id="backfills" title="Backfills" to={urlForStatus([], RunsFeedView.BACKFILLS)} />
      <TabLink
        id="queued"
        title={queuedCount !== null ? `Queued (${queuedCount})` : `Queued`}
        to={urlForStatus(Array.from(queuedStatuses))}
      />
      <TabLink
        id="in-progress"
        title={inProgressCount !== null ? `In progress (${inProgressCount})` : 'In progress'}
        to={urlForStatus(Array.from(inProgressStatuses))}
      />
      <TabLink id="failed" title="Failed" to={urlForStatus(Array.from(failedStatuses))} />
      <TabLink
        id="scheduled"
        title="Scheduled"
        to={`/runs/scheduled?${view === RunsFeedView.RUNS ? 'view=RUNS' : ''}`}
      />
    </Tabs>
  );

  return {tabs, queryResult};
};

export const ActivatableButton = styled(AnchorButton)<{$active: boolean}>`
  color: ${Colors.textLight()};

  &&:hover {
    color: ${Colors.textLight()};
  }

  ${({$active}) =>
    $active
      ? css`
          background-color: ${Colors.backgroundLighterHover()};
          color: ${Colors.textDefault()};

          &&:hover {
            background-color: ${Colors.backgroundLighterHover()};
            color: ${Colors.textDefault()};
          }
        `
      : css`
          background-color: ${Colors.backgroundDefault()};
        `}
`;

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
