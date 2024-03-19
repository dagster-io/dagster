import {Box, Heading, PageHeader} from '@dagster-io/ui-components';

import {AutomationTabs} from './AutomationTabs';
import {useTrackPageView} from '../app/analytics';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {OverviewSensors} from '../overview/OverviewSensors';

export const AutomationSensorsRoot = () => {
  useTrackPageView();
  useDocumentTitle('Automation | Sensors');

  return (
    <Box flex={{direction: 'column'}} style={{height: '100%', overflow: 'hidden'}}>
      <PageHeader title={<Heading>Automation</Heading>} tabs={<AutomationTabs tab="sensors" />} />
      <OverviewSensors />
    </Box>
  );
};
