import {gql, useQuery} from '@apollo/client';
import {Colors, JoinedButtons, TokenizingFieldValue} from '@dagster-io/ui-components';
import isEqual from 'lodash/isEqual';
import {useMemo} from 'react';
import {useLocation} from 'react-router-dom';
import styled, {css} from 'styled-components';

import {failedStatuses, inProgressStatuses, queuedStatuses} from './RunStatuses';
import {runsPathWithFilters, useQueryPersistedRunFilters} from './RunsFilterInput';
import {RunTabsCountQuery, RunTabsCountQueryVariables} from './types/RunListTabs.types';
import {RunStatus, RunsFilter} from '../graphql/types';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {AnchorButton} from '../ui/AnchorButton';

const getDocumentTitle = (selected: ReturnType<typeof useSelectedRunsTab>) => {
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

export const useRunListTabs = (filter: RunsFilter = {}) => {
  const queryResult = useQuery<RunTabsCountQuery, RunTabsCountQueryVariables>(
    RUN_TABS_COUNT_QUERY,
    {
      variables: {
        queuedFilter: {...filter, statuses: Array.from(queuedStatuses)},
        inProgressFilter: {...filter, statuses: Array.from(inProgressStatuses)},
      },
    },
  );

  const {data: countData} = queryResult;
  const {queuedCount, inProgressCount} = useMemo(() => {
    return {
      queuedCount:
        countData?.queuedCount?.__typename === 'Runs' ? countData.queuedCount.count : null,
      inProgressCount:
        countData?.inProgressCount?.__typename === 'Runs' ? countData.inProgressCount.count : null,
    };
  }, [countData]);

  const [filterTokens] = useQueryPersistedRunFilters();
  const selectedTab = useSelectedRunsTab(filterTokens);

  useDocumentTitle(getDocumentTitle(selectedTab));

  const urlForStatus = (statuses: RunStatus[]) => {
    const tokensMinusStatus = filterTokens.filter((token) => token.token !== 'status');
    const statusTokens = statuses.map((status) => ({token: 'status' as const, value: status}));
    return runsPathWithFilters([...statusTokens, ...tokensMinusStatus]);
  };

  const tabs = (
    <JoinedButtons>
      <ActivatableButton to={urlForStatus([])} id="all" $active={selectedTab === 'all'}>
        All runs
      </ActivatableButton>
      <ActivatableButton
        to={urlForStatus(Array.from(queuedStatuses))}
        id="queued"
        $active={selectedTab === 'queued'}
      >
        Queued ({queuedCount ?? 'indeterminate'})
      </ActivatableButton>
      <ActivatableButton
        to={urlForStatus(Array.from(inProgressStatuses))}
        id="in-progress"
        $active={selectedTab === 'in-progress'}
      >
        In progress ({inProgressCount ?? 'indeterminate'})
      </ActivatableButton>
      <ActivatableButton
        to={urlForStatus(Array.from(failedStatuses))}
        id="failed"
        $active={selectedTab === 'failed'}
      >
        Failed
      </ActivatableButton>
      <ActivatableButton
        title="Scheduled"
        to="/runs/scheduled"
        id="scheduled"
        $active={selectedTab === 'scheduled'}
      >
        Scheduled
      </ActivatableButton>
    </JoinedButtons>
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

export const useSelectedRunsTab = (filterTokens: TokenizingFieldValue[]) => {
  const {pathname} = useLocation();
  if (pathname === '/runs/timeline') {
    return 'timeline';
  }
  if (pathname === '/runs/scheduled') {
    return 'scheduled';
  }
  if (pathname === '/overview/backfills') {
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

export const RUN_TABS_COUNT_QUERY = gql`
  query RunTabsCountQuery($queuedFilter: RunsFilter!, $inProgressFilter: RunsFilter!) {
    queuedCount: pipelineRunsOrError(filter: $queuedFilter) {
      ... on Runs {
        count
      }
    }
    inProgressCount: pipelineRunsOrError(filter: $inProgressFilter) {
      ... on Runs {
        count
      }
    }
  }
`;
