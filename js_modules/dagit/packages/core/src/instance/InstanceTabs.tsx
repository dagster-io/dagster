import {gql, QueryResult, useQuery} from '@apollo/client';
import * as React from 'react';

import {QueryCountdown} from '../app/QueryCountdown';
import {Box} from '../ui/Box';
import {Tab, Tabs} from '../ui/Tabs';

import {InstanceConfigHasInfo} from './types/InstanceConfigHasInfo';

const POLL_INTERVAL = 15000;

interface Props<TData> {
  queryData?: QueryResult<TData, any>;
  tab: string;
}

export const InstanceTabs = <TData extends Record<string, any>>(props: Props<TData>) => {
  const {queryData, tab} = props;
  const {data} = useQuery<InstanceConfigHasInfo>(INSTANCE_CONFIG_HAS_INFO);

  return (
    <Box flex={{direction: 'row', justifyContent: 'space-between', alignItems: 'flex-end'}}>
      <Tabs selectedTabId={tab}>
        <Tab id="health" title="Health" to="/instance/health" />
        <Tab id="schedules" title="Schedules" to="/instance/schedules" />
        <Tab id="sensors" title="Sensors" to="/instance/sensors" />
        <Tab id="backfills" title="Backfills" to="/instance/backfills" />
        {data?.instance.hasInfo ? (
          <Tab id="config" title="Configuration" to="/instance/config" />
        ) : null}
      </Tabs>
      {queryData ? (
        <Box padding={{bottom: 8}}>
          <QueryCountdown pollInterval={POLL_INTERVAL} queryResult={queryData} />
        </Box>
      ) : null}
    </Box>
  );
};

const INSTANCE_CONFIG_HAS_INFO = gql`
  query InstanceConfigHasInfo {
    instance {
      hasInfo
    }
  }
`;
