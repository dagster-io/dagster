import {Box, Heading, PageHeader} from '@dagster-io/ui-components';

import {OverviewSchedules} from './OverviewSchedules';
import {OverviewTabs} from './OverviewTabs';
import {useTrackPageView} from '../app/analytics';
import {useDocumentTitle} from '../hooks/useDocumentTitle';

export const OverviewSchedulesRoot = () => {
  useTrackPageView();
  useDocumentTitle('Overview | Schedules');

  return (
    <Box flex={{direction: 'column'}} style={{height: '100%', overflow: 'hidden'}}>
      <PageHeader title={<Heading>Overview</Heading>} tabs={<OverviewTabs tab="schedules" />} />
      <OverviewSchedules />
    </Box>
  );
};
