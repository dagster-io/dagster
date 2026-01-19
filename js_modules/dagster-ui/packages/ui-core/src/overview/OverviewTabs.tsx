import {Box, Colors, Spinner, Tabs} from '@dagster-io/ui-components';
import {useContext} from 'react';
import {observeEnabled} from 'shared/app/observeEnabled.oss';

import {QueryResult} from '../apollo-client';
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

  const automaterialize = useAutomaterializeDaemonStatus();
  const automaterializeSensorsFlagState = useAutoMaterializeSensorFlag();
  const {enableAssetHealthOverviewPreview} = useContext(AssetFeatureContext);
  const hideAMPTab = observeEnabled();

  return (
    <Box flex={{direction: 'row', justifyContent: 'space-between', alignItems: 'flex-end'}}>
      <Tabs selectedTabId={tab}>
        <TabLink id="activity" title="时间线" to="/overview/activity" />
        {enableAssetHealthOverviewPreview && (
          <TabLink id="asset-health" title="资产健康" to="/overview/asset-health" />
        )}
        {automaterializeSensorsFlagState === 'has-global-amp' && !hideAMPTab ? (
          <TabLink
            id="amp"
            title={
              <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
                <div>自动物化</div>
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
        <TabLink id="resources" title="资源" to="/overview/resources" />
      </Tabs>
      {refreshState ? (
        <Box style={{alignSelf: 'center'}}>
          <QueryRefreshCountdown refreshState={refreshState} />
        </Box>
      ) : null}
    </Box>
  );
};
