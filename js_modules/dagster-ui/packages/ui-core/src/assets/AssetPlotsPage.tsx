import {Box, Subtitle} from '@dagster-io/ui-components';
import {useEffect} from 'react';

import {AssetPlots} from './AssetPlots';
import {useTrackEvent} from '../app/analytics';

export const AssetPlotsPage = (props: React.ComponentProps<typeof AssetPlots>) => {
  // Track the event explicitly because the tab is based on a querystring, so the typical
  // pageview event would not be matched to the Plots tab.
  const trackEvent = useTrackEvent();
  useEffect(() => trackEvent('viewAssetPlots'), [trackEvent]);

  return (
    <div>
      <Box
        flex={{justifyContent: 'space-between', alignItems: 'center'}}
        border="bottom"
        padding={{vertical: 16, left: 24, right: 12}}
        style={{marginBottom: -1}}
      >
        <Subtitle>Asset plots</Subtitle>
      </Box>
      <AssetPlots {...props} />
    </div>
  );
};
