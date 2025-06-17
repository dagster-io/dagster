import {Box, PageHeader, Subtitle1} from '@dagster-io/ui-components';

import {OverviewTabs} from './OverviewTabs';
import {useTrackPageView} from '../app/analytics';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {JobsPageContent} from '../jobs/JobsPageContent';

export const OverviewJobsRoot = () => {
  useTrackPageView();
  useDocumentTitle('Overview | Jobs');

  return (
    <Box flex={{direction: 'column'}} style={{height: '100%', overflow: 'hidden'}}>
      <PageHeader title={<Subtitle1>Overview</Subtitle1>} tabs={<OverviewTabs tab="jobs" />} />
      <JobsPageContent />
    </Box>
  );
};
