import {Box, Tabs} from '@dagster-io/ui-components';
import {useContext} from 'react';

import {QueryResult} from '../apollo-client';
import {QueryRefreshCountdown, RefreshState} from '../app/QueryRefresh';
import {AssetFeatureContext} from '../assets/AssetFeatureContext';
import {TabLink} from '../ui/TabLink';

interface Props<TData> {
  refreshState?: RefreshState;
  queryData?: QueryResult<TData, any>;
  tab: string;
}

export const OverviewTabs = <TData extends Record<string, any>>(props: Props<TData>) => {
  const {refreshState, tab} = props;
  const {enableAssetHealthOverviewPreview} = useContext(AssetFeatureContext);

  return (
    <Box flex={{direction: 'row', justifyContent: 'space-between', alignItems: 'flex-end'}}>
      <Tabs selectedTabId={tab}>
        <TabLink id="activity" title="Timeline" to="/overview/activity" />
        {enableAssetHealthOverviewPreview && (
          <TabLink id="asset-health" title="Asset health" to="/overview/asset-health" />
        )}
        <TabLink id="resources" title="Resources" to="/overview/resources" />
      </Tabs>
      {refreshState ? (
        <Box style={{alignSelf: 'center'}}>
          <QueryRefreshCountdown refreshState={refreshState} />
        </Box>
      ) : null}
    </Box>
  );
};
