import {Alert, Box, Heading, PageHeader} from '@dagster-io/ui-components';
import React, {useContext} from 'react';

import {OverviewTabs} from './OverviewTabs';
import {CloudOSSContext} from '../app/CloudOSSContext';
import {useAutoMaterializeSensorFlag} from '../assets/AutoMaterializeSensorFlag';
import {useStateWithStorage} from '../hooks/useStateWithStorage';

export const OverviewPageHeader = ({
  tab,
  queryData,
  refreshState,
  ...rest
}: React.ComponentProps<typeof OverviewTabs> &
  Omit<React.ComponentProps<typeof PageHeader>, 'title'>) => {
  const {showGlobalAMPToSensorAMPBanner} = useContext(CloudOSSContext);
  const [isBannerHidden, setIsBannerHidden] = useStateWithStorage<'1' | undefined>(
    'banner:showGlobalAMPToSensorAMPBanner',
    (key) => key,
  );
  const isSensorAMP = useAutoMaterializeSensorFlag() === 'has-sensor-amp';
  return (
    <PageHeader
      title={<Heading>Overview</Heading>}
      tabs={
        <Box flex={{direction: 'column', gap: 8}}>
          <OverviewTabs tab={tab} queryData={queryData} refreshState={refreshState} />
          {isSensorAMP && showGlobalAMPToSensorAMPBanner && isBannerHidden !== '1' ? (
            <Alert
              title="Looking for the Auto-materialize tab?"
              description="You can find your auto-materialize sensors on the Sensors tab."
              onClose={() => {
                setIsBannerHidden('1');
              }}
            />
          ) : null}
        </Box>
      }
      {...rest}
    />
  );
};
