import {QueryResult} from '@apollo/client';
import {Box, Tabs} from '@dagster-io/ui';
import * as React from 'react';

import {useFeatureFlags} from '../app/Flags';
import {QueryRefreshCountdown, QueryRefreshState} from '../app/QueryRefresh';
import {TabLink} from '../ui/TabLink';

interface Props<TData> {
  refreshState?: QueryRefreshState;
  queryData?: QueryResult<TData, any>;
  tab: string;
}

export const OverviewTabs = <TData extends Record<string, any>>(props: Props<TData>) => {
  const {refreshState, tab} = props;
  const {flagSidebarResources} = useFeatureFlags();

  return (
    <Box flex={{direction: 'row', justifyContent: 'space-between', alignItems: 'flex-end'}}>
      <Tabs selectedTabId={tab}>
        <TabLink id="timeline" title="Timeline" to="/overview/timeline" />
        <TabLink id="jobs" title="Jobs" to="/overview/jobs" />
        <TabLink id="schedules" title="Schedules" to="/overview/schedules" />
        <TabLink id="sensors" title="Sensors" to="/overview/sensors" />
        {flagSidebarResources && (
          <TabLink id="resources" title="Resources" to="/overview/resources" />
        )}
        <TabLink id="backfills" title="Backfills" to="/overview/backfills" />
      </Tabs>
      {refreshState ? (
        <Box padding={{bottom: 8}}>
          <QueryRefreshCountdown refreshState={refreshState} />
        </Box>
      ) : null}
    </Box>
  );
};
