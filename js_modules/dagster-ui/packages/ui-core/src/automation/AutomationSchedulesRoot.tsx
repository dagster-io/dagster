import {Box, Heading, PageHeader} from '@dagster-io/ui-components';

import {AutomationTabs} from './AutomationTabs';
import {useTrackPageView} from '../app/analytics';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {OverviewSchedules} from '../overview/OverviewSchedules';

export const AutomationSchedulesRoot = () => {
  useTrackPageView();
  useDocumentTitle('Automation | Schedules');

  return (
    <Box flex={{direction: 'column'}} style={{height: '100%', overflow: 'hidden'}}>
      <PageHeader title={<Heading>Automation</Heading>} tabs={<AutomationTabs tab="schedules" />} />
      <OverviewSchedules />
    </Box>
  );
};
