import {useQuery} from '@apollo/client';
import {PageHeader, Heading, Box} from '@dagster-io/ui';
import * as React from 'react';

import {
  FIFTEEN_SECONDS,
  QueryRefreshCountdown,
  QueryRefreshState,
  useMergedRefresh,
  useQueryRefreshAtInterval,
} from '../app/QueryRefresh';

import {RunListTabs, RUN_TABS_COUNT_QUERY} from './RunListTabs';
import {inProgressStatuses, queuedStatuses} from './RunStatuses';
import {runsFilterForSearchTokens, useQueryPersistedRunFilters} from './RunsFilterInput';
import {RunTabsCountQuery, RunTabsCountQueryVariables} from './types/RunTabsCountQuery';

interface Props {
  refreshStates: QueryRefreshState[];
}

export const RunsPageHeader = (props: Props) => {
  const {refreshStates} = props;

  const [filterTokens] = useQueryPersistedRunFilters();
  const filter = runsFilterForSearchTokens(filterTokens);

  const runCountResult = useQuery<RunTabsCountQuery, RunTabsCountQueryVariables>(
    RUN_TABS_COUNT_QUERY,
    {
      variables: {
        queuedFilter: {...filter, statuses: Array.from(queuedStatuses)},
        inProgressFilter: {...filter, statuses: Array.from(inProgressStatuses)},
      },
    },
  );

  const {data: countData} = runCountResult;
  const {queuedCount, inProgressCount} = React.useMemo(() => {
    return {
      queuedCount:
        countData?.queuedCount?.__typename === 'Runs' ? countData.queuedCount.count : null,
      inProgressCount:
        countData?.inProgressCount?.__typename === 'Runs' ? countData.inProgressCount.count : null,
    };
  }, [countData]);

  const countRefreshState = useQueryRefreshAtInterval(runCountResult, FIFTEEN_SECONDS);

  const refreshState = useMergedRefresh(countRefreshState, ...refreshStates);

  return (
    <PageHeader
      title={<Heading>Runs</Heading>}
      tabs={
        <Box flex={{direction: 'row', justifyContent: 'space-between', alignItems: 'flex-end'}}>
          <RunListTabs queuedCount={queuedCount} inProgressCount={inProgressCount} />
          <Box padding={{bottom: 8}}>
            <QueryRefreshCountdown refreshState={refreshState} />
          </Box>
        </Box>
      }
    />
  );
};
