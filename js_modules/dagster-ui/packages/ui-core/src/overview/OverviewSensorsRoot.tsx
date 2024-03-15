import {Box, Heading, PageHeader} from '@dagster-io/ui-components';

import {OverviewSensors} from './OverviewSensors';
import {OverviewTabs} from './OverviewTabs';
import {useTrackPageView} from '../app/analytics';
import {useDocumentTitle} from '../hooks/useDocumentTitle';

export const OverviewSensorsRoot = () => {
  useTrackPageView();
  useDocumentTitle('Overview | Sensors');

  return (
    <Box flex={{direction: 'column'}} style={{height: '100%', overflow: 'hidden'}}>
      <PageHeader title={<Heading>Overview</Heading>} tabs={<OverviewTabs tab="sensors" />} />
      <OverviewSensors />
    </Box>
  );
};
