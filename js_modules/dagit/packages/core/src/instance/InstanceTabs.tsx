import {QueryResult} from '@apollo/client';
import {Box, Tab, Tabs} from '@dagster-io/ui';
import * as React from 'react';

import {useFeatureFlags} from '../app/Flags';
import {QueryCountdown} from '../app/QueryCountdown';

import {useCanSeeConfig} from './useCanSeeConfig';

const POLL_INTERVAL = 15000;

interface Props<TData> {
  queryData?: QueryResult<TData, any>;
  tab: string;
}

export const InstanceTabs = <TData extends Record<string, any>>(props: Props<TData>) => {
  const {queryData, tab} = props;
  const canSeeConfig = useCanSeeConfig();
  const {flagInstanceOverview} = useFeatureFlags();

  return (
    <Box flex={{direction: 'row', justifyContent: 'space-between', alignItems: 'flex-end'}}>
      <Tabs selectedTabId={tab}>
        {flagInstanceOverview ? (
          <Tab id="overview" title="Overview" to="/instance/overview" />
        ) : null}
        <Tab id="health" title="Health" to="/instance/health" />
        <Tab id="schedules" title="Schedules" to="/instance/schedules" />
        <Tab id="sensors" title="Sensors" to="/instance/sensors" />
        <Tab id="backfills" title="Backfills" to="/instance/backfills" />
        {canSeeConfig ? <Tab id="config" title="Configuration" to="/instance/config" /> : null}
      </Tabs>
      {queryData ? (
        <Box padding={{bottom: 8}}>
          <QueryCountdown pollInterval={POLL_INTERVAL} queryResult={queryData} />
        </Box>
      ) : null}
    </Box>
  );
};
