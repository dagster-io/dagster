import {Colors, Tabs, TokenizingFieldValue} from '@dagster-io/ui-components';
import isEqual from 'lodash/isEqual';
import {useMemo} from 'react';
import {useLocation} from 'react-router-dom';
import styled, {css} from 'styled-components';

import {failedStatuses, inProgressStatuses, queuedStatuses} from './RunStatuses';
import {getRunFeedPath} from './RunsFeedUtils';
import {runsPathWithFilters, useQueryPersistedRunFilters} from './RunsFilterInput';
import {RunFeedTabsCountQuery, RunFeedTabsCountQueryVariables} from './types/RunsFeedTabs.types';
import {gql, useQuery} from '../apollo-client';
import {RunStatus, RunsFilter} from '../graphql/types';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {AnchorButton} from '../ui/AnchorButton';
import {TabLink} from '../ui/TabLink';

const getDocumentTitle = (selected: ReturnType<typeof useSelectedRunsFeedTab>) => {
  switch (selected) {
    case 'all':
      return 'Runs | All runs';
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

export const useRunsFeedTabs = (filter: RunsFilter = {}, includeRunsFromBackfills: boolean) => {
  const queryResult = useQuery<RunFeedTabsCountQuery, RunFeedTabsCountQueryVariables>(
    RUN_FEED_TABS_COUNT_QUERY,
    {
      variables: {
        queuedFilter: {...filter, statuses: Array.from(queuedStatuses)},
        inProgressFilter: {...filter, statuses: Array.from(inProgressStatuses)},
        includeRunsFromBackfills,
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
  const selectedTab = useSelectedRunsFeedTab(filterTokens);

  useDocumentTitle(getDocumentTitle(selectedTab));

  const urlForStatus = (statuses: RunStatus[]) => {
    const tokensMinusStatus = filterTokens.filter((token) => token.token !== 'status');
    const statusTokens = statuses.map((status) => ({token: 'status' as const, value: status}));
    return runsPathWithFilters(
      [...statusTokens, ...tokensMinusStatus],
      getRunFeedPath(),
      includeRunsFromBackfills,
    );
  };

  const tabs = (
    <Tabs selectedTabId={selectedTab}>
      <TabLink id="all" title="All runs" to={urlForStatus([])} />
      <TabLink
        id="queued"
        title={`Queued (${queuedCount})`}
        to={urlForStatus(Array.from(queuedStatuses))}
      />
      <TabLink
        id="in-progress"
        title={`In progress (${inProgressCount})`}
        to={urlForStatus(Array.from(inProgressStatuses))}
      />
      <TabLink id="failed" title="Failed" to={urlForStatus(Array.from(failedStatuses))} />
      <TabLink
        id="scheduled"
        title="Scheduled"
        to={`${getRunFeedPath()}scheduled?${
          includeRunsFromBackfills ? 'show_runs_within_backfills=true' : ''
        }`}
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

export const useSelectedRunsFeedTab = (filterTokens: TokenizingFieldValue[]) => {
  const {pathname} = useLocation();
  if (pathname === `${getRunFeedPath()}scheduled`) {
    return 'scheduled';
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
    $includeRunsFromBackfills: Boolean!
  ) {
    queuedCount: runsFeedCountOrError(
      filter: $queuedFilter
      includeRunsFromBackfills: $includeRunsFromBackfills
    ) {
      ... on RunsFeedCount {
        count
      }
    }
    inProgressCount: runsFeedCountOrError(
      filter: $inProgressFilter
      includeRunsFromBackfills: $includeRunsFromBackfills
    ) {
      ... on RunsFeedCount {
        count
      }
    }
  }
`;
