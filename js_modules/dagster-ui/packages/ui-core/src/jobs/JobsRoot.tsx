import {Box, Heading, PageHeader} from '@dagster-io/ui-components';

import {JobsPageContent} from './JobsPageContent';
import {useTrackPageView} from '../app/analytics';
import {useDocumentTitle} from '../hooks/useDocumentTitle';

export const JobsRoot = () => {
  useTrackPageView();
  useDocumentTitle('Jobs');

  return (
    <Box flex={{direction: 'column'}} style={{height: '100%', overflow: 'hidden'}}>
      <PageHeader title={<Heading>Jobs</Heading>} />
      <JobsPageContent />
    </Box>
  );
};

// Imported via React.lazy, which requires a default export.
// eslint-disable-next-line import/no-default-export
export default JobsRoot;
