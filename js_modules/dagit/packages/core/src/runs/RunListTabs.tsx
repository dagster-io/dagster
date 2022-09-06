import {gql, useQuery} from '@apollo/client';
import {Tabs, TokenizingFieldValue} from '@dagster-io/ui';
import isEqual from 'lodash/isEqual';
import * as React from 'react';
import {useLocation} from 'react-router-dom';

import {useFeatureFlags} from '../app/Flags';
import {RunStatus} from '../types/globalTypes';
import {TabLink} from '../ui/TabLink';

import {doneStatuses, inProgressStatuses, queuedStatuses} from './RunStatuses';
import {
  runsFilterForSearchTokens,
  runsPathWithFilters,
  useQueryPersistedRunFilters,
} from './RunsFilterInput';
import {RunTabsCountQuery, RunTabsCountQueryVariables} from './types/RunTabsCountQuery';

export const RunListTabs = React.memo(() => {
  const {flagNewWorkspace} = useFeatureFlags();
  const [filterTokens] = useQueryPersistedRunFilters();
  const runsFilter = runsFilterForSearchTokens(filterTokens);

  const {data} = useQuery<RunTabsCountQuery, RunTabsCountQueryVariables>(RUN_TABS_COUNT_QUERY, {
    variables: {
      queuedFilter: {...runsFilter, statuses: Array.from(queuedStatuses)},
      inProgressFilter: {...runsFilter, statuses: Array.from(inProgressStatuses)},
    },
  });

  const counts = React.useMemo(() => {
    return {
      queued: data?.queuedCount?.__typename === 'Runs' ? data.queuedCount.count : null,
      inProgress: data?.inProgressCount?.__typename === 'Runs' ? data.inProgressCount.count : null,
    };
  }, [data]);

  const selectedTab = useSelectedRunsTab(filterTokens);

  const urlForStatus = (statuses: RunStatus[]) => {
    const tokensMinusStatus = filterTokens.filter((token) => token.token !== 'status');
    const statusTokens = statuses.map((status) => ({token: 'status' as const, value: status}));
    return runsPathWithFilters([...statusTokens, ...tokensMinusStatus]);
  };

  return (
    <Tabs selectedTabId={selectedTab} id="run-tabs">
      {flagNewWorkspace ? (
        <TabLink title="Timeline" to="/instance/runs/timeline" id="timeline" />
      ) : null}
      <TabLink title="All runs" to={urlForStatus([])} id="all" />
      <TabLink
        title="Queued"
        count={counts.queued ?? 'indeterminate'}
        to={urlForStatus(Array.from(queuedStatuses))}
        id="queued"
      />
      <TabLink
        title="In progress"
        count={counts.inProgress ?? 'indeterminate'}
        to={urlForStatus(Array.from(inProgressStatuses))}
        id="in-progress"
      />
      <TabLink title="Done" to={urlForStatus(Array.from(doneStatuses))} id="done" />
      <TabLink title="Scheduled" to="/instance/runs/scheduled" id="scheduled" />
      {flagNewWorkspace ? (
        <TabLink title="Backfills" to="/instance/backfills" id="backfills" />
      ) : null}
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

const RUN_TABS_COUNT_QUERY = gql`
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
