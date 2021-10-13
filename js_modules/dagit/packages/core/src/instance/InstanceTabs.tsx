import {QueryResult} from '@apollo/client';
import * as React from 'react';

import {QueryCountdown} from '../app/QueryCountdown';
import {Box} from '../ui/Box';
import {Tab, Tabs} from '../ui/Tabs';

const POLL_INTERVAL = 15000;

interface Props {
  queryData?: QueryResult;
  tab: string;
}

export const InstanceTabs: React.FC<Props> = (props) => {
  const {queryData, tab} = props;
  return (
    <Box flex={{direction: 'row', justifyContent: 'space-between', alignItems: 'flex-end'}}>
      <Tabs selectedTabId={tab}>
        <Tab id="health" title="Health" to="/instance/health" />
        <Tab id="schedules" title="Schedules" to="/instance/schedules" />
        <Tab id="sensors" title="Sensors" to="/instance/sensors" />
        <Tab id="backfills" title="Backfills" to="/instance/backfills" />
        <Tab id="config" title="Configuration" to="/instance/config" />
      </Tabs>
      {queryData ? (
        <Box padding={{bottom: 8}}>
          <QueryCountdown pollInterval={POLL_INTERVAL} queryResult={queryData} />
        </Box>
      ) : null}
    </Box>
  );
};
