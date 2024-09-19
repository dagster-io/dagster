import {Box, Heading, PageHeader} from '@dagster-io/ui-components';

import {OverviewTabs} from './OverviewTabs';
import {useTrackPageView} from '../app/analytics';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {JobsPageContent} from '../jobs/JobsPageContent';

export const OverviewJobsRoot = () => {
  useTrackPageView();
  useDocumentTitle('Overview | Jobs');

  return (
    <Box flex={{direction: 'column'}} style={{height: '100%', overflow: 'hidden'}}>
      <PageHeader title={<Heading>Overview</Heading>} tabs={<OverviewTabs tab="jobs" />} />
      <JobsPageContent />
    </Box>
  );
};
