import {gql} from '@apollo/client';
import {Tabs, TokenizingFieldValue} from '@dagster-io/ui';
import isEqual from 'lodash/isEqual';
import * as React from 'react';
import {useLocation} from 'react-router-dom';

import {RunStatus} from '../types/globalTypes';
import {TabLink} from '../ui/TabLink';

import {doneStatuses, inProgressStatuses, queuedStatuses} from './RunStatuses';
import {runsPathWithFilters, useQueryPersistedRunFilters} from './RunsFilterInput';

interface Props {
  queuedCount: number | null;
  inProgressCount: number | null;
}

export const RunListTabs: React.FC<Props> = React.memo(({queuedCount, inProgressCount}) => {
  const [filterTokens] = useQueryPersistedRunFilters();
  const selectedTab = useSelectedRunsTab(filterTokens);

  const urlForStatus = (statuses: RunStatus[]) => {
    const tokensMinusStatus = filterTokens.filter((token) => token.token !== 'status');
    const statusTokens = statuses.map((status) => ({token: 'status' as const, value: status}));
    return runsPathWithFilters([...statusTokens, ...tokensMinusStatus]);
  };

  return (
    <Tabs selectedTabId={selectedTab} id="run-tabs">
      <TabLink title="All runs" to={urlForStatus([])} id="all" />
      <TabLink
        title="Queued"
        count={queuedCount ?? 'indeterminate'}
        to={urlForStatus(Array.from(queuedStatuses))}
        id="queued"
      />
      <TabLink
        title="In progress"
        count={inProgressCount ?? 'indeterminate'}
        to={urlForStatus(Array.from(inProgressStatuses))}
        id="in-progress"
      />
      <TabLink title="Done" to={urlForStatus(Array.from(doneStatuses))} id="done" />
      <TabLink title="Scheduled" to="/instance/runs/scheduled" id="scheduled" />
    </Tabs>
  );
});

export const useSelectedRunsTab = (filterTokens: TokenizingFieldValue[]) => {
  const {pathname} = useLocation();
  if (pathname === '/instance/runs/timeline') {
    return 'timeline';
  }
  if (pathname === '/instance/runs/scheduled') {
    return 'scheduled';
  }
  if (pathname === '/instance/backfills') {
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
  if (isEqual(doneStatuses, statusTokens)) {
    return 'done';
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
