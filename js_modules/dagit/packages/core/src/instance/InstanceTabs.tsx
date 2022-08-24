import {QueryResult} from '@apollo/client';
import {Box, Tabs} from '@dagster-io/ui';
import * as React from 'react';

import {useFeatureFlags} from '../app/Flags';
import {QueryRefreshCountdown, QueryRefreshState} from '../app/QueryRefresh';
import {TabLink} from '../ui/TabLink';

import {InstancePageContext} from './InstancePageContext';
import {useCanSeeConfig} from './useCanSeeConfig';

interface Props<TData> {
  refreshState?: QueryRefreshState;
  queryData?: QueryResult<TData, any>;
  tab: string;
}

// todo dish: Delete this once Cloud is switched to use `InstancePageContext`.
export const InstanceTabContext = React.createContext({healthTitle: 'Daemons'});

export const InstanceTabs = <TData extends Record<string, any>>(props: Props<TData>) => {
  const {refreshState, tab} = props;

  const {healthTitle} = React.useContext(InstancePageContext);
  const {flagNewWorkspace} = useFeatureFlags();
  const canSeeConfig = useCanSeeConfig();

  return (
    <Box flex={{direction: 'row', justifyContent: 'space-between', alignItems: 'flex-end'}}>
      <Tabs selectedTabId={tab}>
        <TabLink id="overview" title="Overview" to="/instance/overview" />
        {flagNewWorkspace ? (
          <TabLink id="code-locations" title="Code locations" to="/instance/code-locations" />
        ) : null}
        <TabLink id="health" title={healthTitle} to="/instance/health" />
        <TabLink id="schedules" title="Schedules" to="/instance/schedules" />
        <TabLink id="sensors" title="Sensors" to="/instance/sensors" />
        <TabLink id="backfills" title="Backfills" to="/instance/backfills" />
        {canSeeConfig ? <TabLink id="config" title="Configuration" to="/instance/config" /> : null}
      </Tabs>
      {refreshState ? (
        <Box padding={{bottom: 8}}>
          <QueryRefreshCountdown refreshState={refreshState} />
        </Box>
      ) : null}
    </Box>
  );
};
