import {QueryResult} from '@apollo/client';
import {Colors, Tabs, Tab} from '@blueprintjs/core';
import * as React from 'react';
import {Link} from 'react-router-dom';

import {QueryCountdown} from '../app/QueryCountdown';
import {Box} from '../ui/Box';

const POLL_INTERVAL = 15000;

interface Props {
  queryData?: QueryResult;
  tab: string;
}

export const InstanceTabs: React.FC<Props> = (props) => {
  const {queryData, tab} = props;
  return (
    <Box
      flex={{direction: 'row', justifyContent: 'space-between', alignItems: 'flex-end'}}
      border={{side: 'bottom', width: 1, color: Colors.LIGHT_GRAY3}}
      margin={{horizontal: 24}}
    >
      <Tabs selectedTabId={tab}>
        <Tab id="health" title={<Link to="/instance/health">Health</Link>} />
        <Tab id="schedules" title={<Link to="/instance/schedules">Schedules</Link>} />
        <Tab id="sensors" title={<Link to="/instance/sensors">Sensors</Link>} />
        <Tab id="backfills" title={<Link to="/instance/backfills">Backfills</Link>} />
        <Tab id="config" title={<Link to="/instance/config">Configuration</Link>} />
      </Tabs>
      {queryData ? (
        <Box padding={{bottom: 8}}>
          <QueryCountdown pollInterval={POLL_INTERVAL} queryResult={queryData} />
        </Box>
      ) : null}
    </Box>
  );
};
