import {Box, Colors, Spinner, Tabs} from '@dagster-io/ui-components';
import {useContext} from 'react';

import {QueryResult} from '../apollo-client';
import {useFeatureFlags} from '../app/Flags';
import {QueryRefreshCountdown, RefreshState} from '../app/QueryRefresh';
import {AssetFeatureContext} from '../assets/AssetFeatureContext';
import {useAutoMaterializeSensorFlag} from '../assets/AutoMaterializeSensorFlag';
import {useAutomaterializeDaemonStatus} from '../assets/useAutomaterializeDaemonStatus';
import {TabLink} from '../ui/TabLink';

interface Props<TData> {
  refreshState?: RefreshState;
  queryData?: QueryResult<TData, any>;
  tab: string;
}

export const OverviewTabs = <TData extends Record<string, any>>(props: Props<TData>) => {
  const {refreshState, tab} = props;

  const {flagLegacyNav, flagLegacyRunsPage} = useFeatureFlags();

  const automaterialize = useAutomaterializeDaemonStatus();
  const automaterializeSensorsFlagState = useAutoMaterializeSensorFlag();
  const {enableAssetHealthOverviewPreview} = useContext(AssetFeatureContext);

  return (
    <Box flex={{direction: 'row', justifyContent: 'space-between', alignItems: 'flex-end'}}>
      <Tabs selectedTabId={tab}>
        <TabLink id="activity" title="Timeline" to="/overview/activity" />
        {enableAssetHealthOverviewPreview && (
          <TabLink id="asset-health" title="Asset health" to="/overview/asset-health" />
        )}
        {/* These are flagged individually because the links must be children of `Tabs`: */}
        {flagLegacyNav ? <TabLink id="jobs" title="Jobs" to="/overview/jobs" /> : null}
        {flagLegacyNav ? (
          <TabLink id="schedules" title="Schedules" to="/overview/schedules" />
        ) : null}
        {flagLegacyNav ? <TabLink id="sensors" title="Sensors" to="/overview/sensors" /> : null}
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
                        automaterialize.paused === false
                          ? Colors.accentBlue()
                          : Colors.accentGray(),
                    }}
                  />
                )}
              </Box>
            }
            to="/overview/automation"
          />
        ) : null}
        <TabLink id="resources" title="Resources" to="/overview/resources" />
        {flagLegacyRunsPage ? (
          <TabLink id="backfills" title="Backfills" to="/overview/backfills" />
        ) : null}
      </Tabs>
      {refreshState ? (
        <Box style={{alignSelf: 'center'}}>
          <QueryRefreshCountdown refreshState={refreshState} />
        </Box>
      ) : null}
    </Box>
  );
};
