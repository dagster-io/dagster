import {QueryResult} from '@apollo/client';
import {Box, Spinner, Tabs, colorAccentBlue, colorAccentGray} from '@dagster-io/ui-components';
import * as React from 'react';

import {QueryRefreshCountdown, QueryRefreshState} from '../app/QueryRefresh';
import {useAutomaterializeDaemonStatus} from '../assets/AutomaterializeDaemonStatusTag';
import {useAutomationPolicySensorFlag} from '../assets/AutomationPolicySensorFlag';
import {TabLink} from '../ui/TabLink';

interface Props<TData> {
  refreshState?: QueryRefreshState;
  queryData?: QueryResult<TData, any>;
  tab: string;
}

export const OverviewTabs = <TData extends Record<string, any>>(props: Props<TData>) => {
  const {refreshState, tab} = props;

  const automaterialize = useAutomaterializeDaemonStatus();
  const automaterializeSensorsFlagState = useAutomationPolicySensorFlag();

  return (
    <Box flex={{direction: 'row', justifyContent: 'space-between', alignItems: 'flex-end'}}>
      <Tabs selectedTabId={tab}>
        <TabLink id="activity" title="Activity" to="/overview/activity" />
        <TabLink id="jobs" title="Jobs" to="/overview/jobs" />
        <TabLink id="schedules" title="Schedules" to="/overview/schedules" />
        <TabLink id="sensors" title="Sensors" to="/overview/sensors" />
        {automaterializeSensorsFlagState === 'has-global-amp' ? (
          <TabLink
            id="amp"
            title={
              <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
                <div>Auto-materialize</div>
                {automaterialize.loading ? (
                  <Spinner purpose="body-text" />
                ) : (
                  <div
                    style={{
                      width: '10px',
                      height: '10px',
                      borderRadius: '50%',
                      backgroundColor:
                        automaterialize.paused === false ? colorAccentBlue() : colorAccentGray(),
                    }}
                  />
                )}
              </Box>
            }
            to="/overview/automaterialize"
          />
        ) : null}
        <TabLink id="resources" title="Resources" to="/overview/resources" />
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
